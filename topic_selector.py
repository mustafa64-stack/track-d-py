
import json
from pathlib import Path


def load_topics(topic_tree_path="topic_tree.json"):
    """Load topics from the existing topic tree."""
    path = Path(topic_tree_path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    topics = data.get("topics", [])

    if not isinstance(topics, list):
        raise ValueError("The topic tree must contain a list of topics.")

    return topics


def select_next_topic(
    topics,
    mastery_by_topic,
    threshold=0.80,
):
    """
    Select the next topic for practice.

    Rules:
    1. Prioritize assessed topics below the mastery threshold.
    2. Among those topics, select the lowest mastery.
    3. If no assessed topic needs practice, select an unassessed topic.
    4. If all topics meet the threshold, return None.

    mastery_by_topic should contain only topics with recorded
    mastery scores, with values between 0.0 and 1.0.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Threshold must be between 0 and 1.")

    if not topics:
        return None

    topic_by_id = {}

    for topic in topics:
        topic_id = topic.get("topic_id")

        if not topic_id:
            continue

        topic_by_id[topic_id] = topic

    # Validate recorded mastery scores.
    for topic_id, mastery in mastery_by_topic.items():
        if topic_id not in topic_by_id:
            raise ValueError(
                f"Unknown topic ID in mastery data: {topic_id}"
            )

        if not isinstance(mastery, (int, float)):
            raise ValueError(
                f"Mastery for {topic_id} must be numeric."
            )

        if not 0.0 <= mastery <= 1.0:
            raise ValueError(
                f"Mastery for {topic_id} must be between 0 and 1."
            )

    # First: find assessed topics that still need practice.
    needs_practice = [
        (mastery, topic_by_id[topic_id])
        for topic_id, mastery in mastery_by_topic.items()
        if mastery < threshold
    ]

    if needs_practice:
        needs_practice.sort(
            key=lambda item: (item[0], item[1]["topic_id"])
        )
        return needs_practice[0][1]

    # Second: give unassessed topics a chance to be assessed.
    unassessed = [
        topic
        for topic_id, topic in topic_by_id.items()
        if topic_id not in mastery_by_topic
    ]

    if unassessed:
        unassessed.sort(key=lambda topic: topic["topic_id"])
        return unassessed[0]

    # All topics have been assessed and meet the threshold.
    return None


if __name__ == "__main__":
    topics = load_topics()

    # Example scores: these are illustrative, not real learner data.
    example_mastery = {
        "vector_multiplication": 0.75,
        "multidimensional_derivatives": 0.30,
    }

    print(f"Topics loaded: {len(topics)}")
    print(f"Topics assessed: {len(example_mastery)}")

    selected = select_next_topic(
        topics=topics,
        mastery_by_topic=example_mastery,
        threshold=0.80,
    )

    if selected:
        print("\nNext topic:", selected["name"])
        print("Topic ID:", selected["topic_id"])
    else:
        print("\nAll topics meet the mastery threshold.")
