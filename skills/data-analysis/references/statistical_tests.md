# Statistical Tests Reference

## Common Tests

### Compare Two Groups
| Test | Use When |
|------|----------|
| t-test (independent) | Two groups, continuous data, normal distribution |
| t-test (paired) | Before/after measurements |
| Mann-Whitney U | Two groups, non-normal data |
| Chi-square | Categorical data |

### Compare Multiple Groups
| Test | Use When |
|------|----------|
| ANOVA | 3+ groups, normal data, equal variance |
| Kruskal-Wallis | 3+ groups, non-normal data |

### Relationships
| Test | Use When |
|------|----------|
| Pearson correlation | Linear relationship, normal data |
| Spearman correlation | Non-linear, ranked data |
| Chi-square test | Association between categorical variables |

## When to Use What

### Continuous Data
- Normal distribution → t-test, ANOVA
- Non-normal → Mann-Whitney, Kruskal-Wallis

### Categorical Data
- Counts/frequencies → Chi-square
- Ordinal → Spearman

### Sample Size
- n < 30 → Non-parametric tests
- n >= 30 → Parametric tests okay

## Effect Sizes

| Size | d value |
|------|---------|
| Small | 0.2 |
| Medium | 0.5 |
| Large | 0.8 |

## P-Values

- p < 0.05 → Statistically significant
- p < 0.01 → Highly significant
- p < 0.001 → Very highly significant
