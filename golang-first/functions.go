package main

import "fmt"
import "errors"
import "math"

func plus(a int, b int) int {

    return a + b
}

func plusPlus(a, b, c int) int {
    return a + b + c
}

// Multiple Return Values
func vals() (int, int) {
    return 3, 7
}


// Variadic Functions
// Variadic functions can be called with any number of trailing arguments. For example, fmt.Println is a common variadic function.
func sum(nums ...int) {
    fmt.Print(nums, " ")
    total := 0

    for _, num := range nums {
        total += num
    }
    fmt.Println(total)
}

// CLOSURES
func intSeq() func() int {
    i := 0
    return func() int {
        i++
        return i
    }
}

// METHOD
// METHOD is a function which takes a receiver (OOP terminology carryover)
// Example #1:
type Triangle struct {
    a, b, c float64
}
func valid(t *Triangle) error {
    if t.a + t.b > t.c && t.a + t.c > t.b && t.b + t.c > t.a {
        return nil
    }
    return errors.New("Triangle is not valid")
}
func perimeter(t *Triangle) (float64, error) {
    err := valid(t)
    if err != nil {
        return -1, err
    }

    return t.a + t.b + t.c, nil
}
func square(t *Triangle) (float64, error) {
    p, err := perimeter(t)
    if err != nil {
        return -1, err
    }

    p /= 2
    s := p * (p - t.a) * (p - t.b) * (p - t.c)
    return math.Sqrt(s), nil
}
// Example #2: 
/*
type rect struct {
    width, height int
}
func (r *rect) area() int {
    return r.width * r.height
}
func (r rect) perim() int {
    return 2*r.width + 2*r.height
}
*/

//===========================
//    MAIN
//===========================
// func main() {
//     functionsMain()
// }

func functionsMain() {

    res := plus(1, 2)
    fmt.Println("1+2 =", res)

    res = plusPlus(1, 2, 3)
    fmt.Println("1+2+3 =", res)

	// Multiple Return Values
	a, b := vals()
    fmt.Println(a)
    fmt.Println(b)

	_, c := vals()
    fmt.Println(c)

	// Variadic Functions
	sum(1, 2)
	sum(1, 2, 3)

	nums := []int{1, 2, 3, 4}
	sum(nums...)

	// CLOSURES
	nextInt := intSeq()
	fmt.Println(nextInt())
    fmt.Println(nextInt())
    fmt.Println(nextInt())
	
	newInts := intSeq()
    fmt.Println(newInts())

    // METHOD
    /*
    r := rect{width: 10, height: 5}
    fmt.Println("area: ", r.area())
    fmt.Println("perim:", r.perim())

    // Go automatically handles conversion between values and pointers for method calls.
    // You may want to use a pointer receiver type to avoid copying on method calls or to allow the method to mutate the receiving struct.
    rp := &r
    fmt.Println("area: ", rp.area())
    fmt.Println("perim:", rp.perim())
    */
}