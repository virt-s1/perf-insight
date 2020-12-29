**Description**

This benchmark report compares the TEST results over the BASE results. The column names of the table consist of two parts. The first part is the KEYs that identifies the specified test case, and the second part is the KPIs as the test results.

KPI is the abbreviation of "Key Performance Indicator", it measures the performance that a test can achieve, and usually reflects the effectiveness of the system. In this table, each KPI is divided into 7 columns. Take "IOPS" as an example, "IOPS" (input/output operations per second) is a typical KPI for storage performance testing. It will be divided into the following seven columns:
1. IOPS-BASE-AVG: The **mean value** of the BASE samples
4. IOPS-BASE-%SD: The **standard deviation in percentage** of the BASE samples
5. IOPS-TEST-AVG: Same as above, but for TEST samples.
6. IOPS-TEST-%SD: Same as above, but for TEST samples.
7. IOPS-%DF: The **differance in percentage** of TEST over BASE samples.
8. IOPS-SGN: The **significance** calculated by the t-test of the two samples.
9. IOPS-CON: The preliminary **conclusion** determined by algorithm.

**About calculations**

- AVG = SUM(the values of all the samples) / COUNT(samples)
- %SD = (The Standard Deviation of all the samples) / AVG * 100%
- %DF = (TEST-AVG - BASE-AVG) / BASE-AVG * 100%
- SGN = 1 - TTEST(all the BASE samples, all the TEST samples)

**About conclusion**

An algorithm helps reaching a preliminary conclusion for each KPI. It could be any of the following ones:

| Abbr | Conclusion             | Reaching Condition (priority decreasing)                 |
| :--- | :--------------------- | :------------------------------------------------------- |
| ID   | Invalid Data           | Any of the input data is invalid.                        |
| HV   | High Variance          | %SD > MAX_PCTDEV_THRESHOLD                               |
| NS   | No Significance        | SGN < CONFIDENCE_THRESHOLD                               |
| NC   | Negligible Changes     | abs(%DF) <= NEGLIGIBLE_THRESHOLD                         |
| MI   | Moderately Improved    | NEGLIGIBLE_THRESHOLD < abs(%DF) <= REGRESSION_THRESHOLD. |
| MR   | Moderately Regressed   | Same as above, but in the negative direction.            |
| DI   | Dramatically Improved  | abs(%DF) > REGRESSION_THRESHOLD                          |
| DR   | Dramatically Regressed | Same as above, but in the negative direction.            |

The following parameters can be specified by users.

| Parameters           | Description                           | Default |
| -------------------- | ------------------------------------- | :------ |
| HIGHER_IS_BETTER     | Describe the direction of improvement | True    |
| MAX_PCTDEV_THRESHOLD | Max %SD can be accepted (0 = disable) | 0.10    |
| CONFIDENCE_THRESHOLD | Min SIG to be considered reproducible | 0.95    |
| NEGLIGIBLE_THRESHOLD | Max %DF can be ignored (0 = disable)  | 0.05    |
| REGRESSION_THRESHOLD | Min %DF to be considered dramatically | 0.10    |
