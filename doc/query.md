- 多个operation时，必须制定operation_name，选择要执行的operation，不能同时选择多个operation

```
query Hello { hello }
query Echo { echo(v: "echo") }
```


- 一个operation，即使batch query时，也可以不指定operation_name
```
query {
    hello
    echo(v: "echo")
}
```
