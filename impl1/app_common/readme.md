# CosmosAIGraph: app_common

Common Python code for this solition is developed and tested here, then 
"deployed" to the several other app_xxx subprojects via the following
Apache Ant command:

```
ant -f deploy_master_code.xml
```

This approach is designed to achieve code-reuse, code-consistency,
and a higher degree of unit-testing.
