# Paper 2 Public Protocol

The public reference evaluates two separate conditions on the same 288 paired-null-
comparable Materials Project elastic cells: positive valid-minus-null R2 and positive
absolute held-out R2. R2 was calculated with `sklearn.metrics.r2_score`, whose
denominator uses the mean of evaluated held-out `y_true`. The demonstrated R2 > 0
boundary is not a universal engineering threshold.
