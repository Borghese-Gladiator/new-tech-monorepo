package main

import "fmt"

// RECURSION
func fact(n int) int {
    if n == 0 {
        return 1
    }
    return n * fact(n-1)
}

// func main() {
//     iterationMain()
// }

func iterationMain() {
	// RECURSION
	fmt.Println(fact(7))

	// Anonymous Functions recursion
	var fib func(n int) int
	fib = func(n int) int {
		if n < 2 {
			return n
		}
		return fib(n-1) + fib(n-2)
	}
	fmt.Println(fib(7))

	// RANGE over built-in types
    nums := []int{2, 3, 4}
    sum := 0
    for _, num := range nums {
        sum += num
    }
    fmt.Println("sum:", sum)

	// iterate over indexes and values
    for i, num := range nums {
        if num == 3 {
            fmt.Println("index:", i)
        }
    }

	// iterate over keys/values
    kvs := map[string]string{"a": "apple", "b": "banana"}
    for k, v := range kvs {
        fmt.Printf("%s -> %s\n", k, v)
    }

	// iterate over keys
    for k := range kvs {
        fmt.Println("key:", k)
    }
	
	// range on strings iterates over Unicode code points. The first value is the starting byte index
	// of the rune and the second the rune itself. See Strings and Runes for more details
    for i, c := range "go" {
        fmt.Println(i, c)
    }
}