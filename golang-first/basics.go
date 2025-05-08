package main

import (
    "fmt"
    "math"
    "time"
)

const globalConstant string = "constant"

// func main() {
//     basicsMain()
// }

func basicsMain() {
    // HELLO WORLD
    fmt.Println("hello world")

    // VALUE TYPES - strings, integers, floats, booleans
    fmt.Println("go" + "lang")
    fmt.Println("1+1 =", 1+1)
    fmt.Println("7.0/3.0 =", 7.0/3.0)
    fmt.Println(true && false)
    fmt.Println(true || false)
    fmt.Println(!true)

    // VARIABLES
    var initialString = "initial"
    fmt.Println(initialString)

    var intOne, intTwo int = 1, 2
    fmt.Println(intOne, intTwo)

    var isAvailable = true
    fmt.Println(isAvailable)

    var defaultInt int
    fmt.Println(defaultInt)

    fruit := "apple"
    fmt.Println(fruit)

    // CONSTANTS
    fmt.Println(globalConstant)

    const bigNumber = 500000000
    const calculatedFloat = 3e20 / bigNumber
    fmt.Println(calculatedFloat)
    fmt.Println(int64(calculatedFloat))
    fmt.Println(math.Sin(bigNumber))

    // LOOPS - for keyword enables for, while, and range loops
    loopCounter := 1
    for loopCounter <= 3 {
        fmt.Println(loopCounter)
        loopCounter++
    }

    for index := 0; index < 3; index++ {
        fmt.Println(index)
    }

    for rangeIndex := range 3 {
        fmt.Println("range", rangeIndex)
    }

    for {
        fmt.Println("loop")
        break
    }

    for oddCheck := range 6 {
        if oddCheck%2 == 0 {
            continue
        }
        fmt.Println(oddCheck)
    }

    // IF/ELSE
    if 7%2 == 0 {
        fmt.Println("7 is even")
    } else {
        fmt.Println("7 is odd")
    }

    if 8%4 == 0 {
        fmt.Println("8 is divisible by 4")
    }

    if 8%2 == 0 || 7%2 == 0 {
        fmt.Println("either 8 or 7 are even")
    }

    // statement precede conditional; any variables declared are available in the block
    if num := 9; num < 0 {
        fmt.Println(num, "is negative")
    } else if num < 10 {
        fmt.Println(num, "has 1 digit")
    } else {
        fmt.Println(num, "has multiple digits")
    }

    // SWITCH
    switchValue := 2
    fmt.Print("Write ", switchValue, " as ")
    switch switchValue {
    case 1:
        fmt.Println("one")
    case 2:
        fmt.Println("two")
    case 3:
        fmt.Println("three")
    }

    switch time.Now().Weekday() {
    case time.Saturday, time.Sunday:
        fmt.Println("It's the weekend")
    default:
        fmt.Println("It's a weekday")
    }

    currentTime := time.Now()
    switch {
    case currentTime.Hour() < 12:
        fmt.Println("It's before noon")
    default:
        fmt.Println("It's after noon")
    }

    // TYPE SWITCH - compares types instead of values
    identifyType := func(val interface{}) {
        switch v := val.(type) {
        case bool:
            fmt.Println("I'm a bool")
        case int:
            fmt.Println("I'm an int")
        default:
            fmt.Printf("Don't know type %T\n", v)
        }
    }

    identifyType(true)
    identifyType(1)
    identifyType("hey")
}
