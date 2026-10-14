-- Supabase setup for Study Companion (Track D)
-- Run this in your Supabase SQL editor to initialize tables and vector search

-- Enable pgvector for storing Gemini embeddings
create extension if not exists vector;

-- Registered course materials (PDF books, lecture decks, YouTube videos)
create table if not exists sources (
    id text primary key,
    title text not null,
    modality text not null check (modality in ('pdf', 'slide', 'youtube', 'image', 'other')),
    created_at timestamptz default now()
);

-- Concept topics extracted from course chunks (used by Member B's BKT model)
create table if not exists topics (
    id text primary key,
    name text not null,
    parent_id text references topics(id) on delete set null,
    created_at timestamptz default now()
);

-- Graph edges defining prerequisite relationships between concepts
create table if not exists prerequisites (
    topic_id text not null references topics(id) on delete cascade,
    prereq_id text not null references topics(id) on delete cascade,
    primary key (topic_id, prereq_id)
);

-- Unified chunks table across all modalities
create table if not exists chunks (
    id text primary key,
    source_id text references sources(id) on delete cascade,
    modality text not null check (modality in ('pdf', 'slide', 'youtube', 'image', 'text')),
    text text not null,
    page integer,
    slide integer,
    start_sec numeric,
    end_sec numeric,
    topic_id text references topics(id) on delete set null,
    image_ref text,
    embedding vector(1000), -- Gemini text-embedding-001 output
    created_at timestamptz default now()
);

-- Standard lookup indexes
create index if not exists idx_chunks_source_id on chunks(source_id);
create index if not exists idx_chunks_topic_id on chunks(topic_id);
create index if not exists idx_chunks_modality on chunks(modality);

-- HNSW index for fast approximate cosine similarity
create index if not exists idx_chunks_embedding_hnsw 
on chunks using hnsw (embedding vector_cosine_ops);

-- Main similarity search function called by retrieval_engine.py
create or replace function match_chunks (
    query_embedding vector(1000),
    match_threshold float default 0.35,
    match_count int default 6,
    filter_topic_id text default null
)
returns table (
    id text,
    source_id text,
    modality text,
    text text,
    page integer,
    slide integer,
    start_sec numeric,
    end_sec numeric,
    topic_id text,
    image_ref text,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        c.id,
        c.source_id,
        c.modality,
        c.text,
        c.page,
        c.slide,
        c.start_sec,
        c.end_sec,
        c.topic_id,
        c.image_ref,
        1 - (c.embedding <=> query_embedding) as similarity
    from chunks c
    where (1 - (c.embedding <=> query_embedding)) >= match_threshold
      and (filter_topic_id is null or c.topic_id = filter_topic_id)
    order by c.embedding <=> query_embedding
    limit match_count;
end;
$$;
