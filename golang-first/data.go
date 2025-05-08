package main

import (
    "fmt"
    "unicode/utf8"
)

// func main() {
//     dataMain()
// }

func dataMain() {
	// STRINGS
	fmt.Println("STRINGS")
    const s = "สวัสดี"

	// RAW BYTES length
	// Since strings are equivalent to []byte, this will produce the length of the raw bytes stored within
    fmt.Println("Len:", len(s))

    for i := 0; i < len(s); i++ {
        fmt.Printf("%x ", s[i])
    }
    fmt.Println()

	// RUNE (HUMAN READABLE CHARACTER) length
	// To count how many runes are in a string, we can use the utf8 package.
	// Note that the run-time of RuneCountInString depends on the size of the
	// string, because it has to decode each UTF-8 rune sequentially.
	// Some Thai characters are represented by UTF-8 code points that can span multiple bytes, so the result of this count may be surprising.
    fmt.Println("Rune count:", utf8.RuneCountInString(s))

    for idx, runeValue := range s {
        fmt.Printf("%#U starts at %d\n", runeValue, idx)
    }

    fmt.Println("\nUsing DecodeRuneInString")
    for i, w := 0, 0; i < len(s); i += w {
        runeValue, width := utf8.DecodeRuneInString(s[i:])
        fmt.Printf("%#U starts at %d\n", runeValue, i)
        w = width

        examineRune(runeValue)
    }
	fmt.Println()

	// STRUCTS
	fmt.Println("STRUCTS")
    fmt.Println(person{"Bob", 20})

    fmt.Println(person{name: "Alice", age: 30})

    fmt.Println(person{name: "Fred"})

    fmt.Println(&person{name: "Ann", age: 40})

    fmt.Println(newPerson("Jon"))

    st := person{name: "Sean", age: 50}
    fmt.Println(st.name)

    sp := &st
    fmt.Println(sp.age)

	// Structs are mutable
    sp.age = 51
    fmt.Println(sp.age)

	// Anonymous Structs
	// Technique common for Table Driven Tests - https://gobyexample.com/testing-and-benchmarking
    dog := struct {
        name   string
        isGood bool
    }{
        "Rex",
        true,
    }
    fmt.Println(dog)
}

type person struct {
    name string
    age  int
}

func newPerson(name string) *person {

    p := person{name: name}
    p.age = 42
    return &p
}

func examineRune(r rune) {
	// Values enclosed in single quotes are rune literals. We can compare a rune value to a rune literal directly.
    if r == 't' {
        fmt.Println("found tee")
    } else if r == 'ส' {
        fmt.Println("found so sua")
    }
}