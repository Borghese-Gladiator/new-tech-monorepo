# Golang
First exposure to Golang. I've heard about super high concurrency and weird error handling, but will be taking a look at writing Go today.

Following [Go by Example](https://gobyexample.com/hello-world) to learn the basics of Go.

## Bootstrap
```
go mod init
go run .
```

## Notes
GoLang is **STRONGLY typed**. It appears weakly typed since it has type inference where it guesses the type of a variable when declared.
```go
f := "apple"
f = 10 // ERROR: cannot assign int to string variable
```

GoLang list of basic types
```
bool

string

int  int8  int16  int32  int64
uint uint8 uint16 uint32 uint64 uintptr
byte // alias for uint8
rune // alias for int32
     // represents a Unicode code point

float32 float64

complex64 complex128
```

GoLang does NOT have a ternary if. Use a full if statement

GoLang has SWITCH statements and TYPE SWITCH statements to compare types

Mixed packages are NOT allowed.
- `package main` - set at top for standalone executable programs
- `main()` - entry point of program
- multiple mains CANNOT be in the same directory

GoLang Slices
- length - number of elements currently in slice (how many items accessible via indexing)
- capacity - total space in underlying array from start of slice to end of array
```go
ab := make([]int, 3, 5) // len = 3, cap = 5
fmt.Println(len(ab))    // 3
fmt.Println(cap(ab))    // 5
```

Function names
- function names declared in one package are all shared

String length
- RAW BYTE length - `len(s)`
- RUNE (Human Readable Character) length - `utf8.RuneCountInString(s)`
