from bkt import update_bkt


def test_correct_answer_increases_mastery():
    old_mastery = 0.30
    new_mastery = update_bkt(old_mastery, True)

    assert new_mastery > old_mastery
    assert 0 <= new_mastery <= 1


def test_wrong_answer_decreases_mastery():
    old_mastery = 0.80
    new_mastery = update_bkt(old_mastery, False)

    assert new_mastery < old_mastery
    assert 0 <= new_mastery <= 1


def test_mastery_stays_between_zero_and_one():
    for mastery in [0.0, 0.2, 0.5, 0.8, 1.0]:
        for correct in [True, False]:
            result = update_bkt(mastery, correct)

            assert 0 <= result <= 1
