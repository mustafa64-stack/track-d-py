def update_bkt(mastery, correct, learn=0.15, slip=0.10, guess=0.20):
    if correct:
        p_correct = mastery * (1 - slip) + (1 - mastery) * guess
        p_known = (mastery * (1 - slip)) / p_correct
    else:
        p_wrong = mastery * slip + (1 - mastery) * (1 - guess)
        p_known = (mastery * slip) / p_wrong

    new_mastery = p_known + (1 - p_known) * learn

    return new_mastery
