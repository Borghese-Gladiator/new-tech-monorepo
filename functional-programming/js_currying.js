//===========================
//   Currying
//===========================
// transform function that takes multiple arguments into a sequence of functions that each take a single argument

// BURGER EXAMPLE
// Currying - default function version
function makeBurgerCurried(bun) {
  return function (patty) {
      return function (topping) {
          return `Your burger has: ${bun} bun, ${patty} patty, and ${topping} topping.`;
      };
  };
}
const chooseBun = makeBurgerCurried("Sesame");
const choosePatty = chooseBun("Mix Veg");
const myCurriedBurger = choosePatty("Cheese");

console.log(myCurriedBurger); // Output: Your burger has: Sesame bun, Mix Veg patty, and Cheese topping.

// Currying - Arrow function version
const  curriedArrowFunction = (bun) => (patty) => (topping) =>
  `Your burger has: ${bun} bun, ${patty} patty, and ${topping} topping`

const myArrowFunction = curriedArrowFunction("Sesame")("Mix Veg")("Cheese")
console.log(myArrowFunction); // Your burger has: Sesame bun, Mix Veg patty, and Cheese topping

// No Currying
function makeBurger(bun, patty, topping) {
  return `Your burger has: ${bun} bun, ${patty} patty, and ${topping} topping.`;
}

const myBurger = makeBurger("Sesame", "Mix Veg", "Cheese");
console.log(myBurger); // Output: Your burger has: Sesame bun, Mix Veg patty, and Cheese topping.

//---------------------------------------------------------------------------------------
// DISCOUNT CALCULATOR example

function createDiscountCalculator(discountRate) {
  return function (price) {
      return price * (1 - discountRate);
  };
}
const regularDiscount = createDiscountCalculator(0.1); // 10% discount
const premiumDiscount = createDiscountCalculator(0.2); // 20% discount
console.log(regularDiscount(100)); // Output: 90
console.log(premiumDiscount(100)); // Output: 80
console.log(regularDiscount(200)); // Output: 180

// No Currying
function calculateDiscount(customerType, price) {
  if (customerType === "Regular") {
      return price * 0.9; // 10% discount
  } else if (customerType === "Premium") {
      return price * 0.8; // 20% discount
  }
}

console.log(calculateDiscount("Regular", 100)); // Output: 90
console.log(calculateDiscount("Premium", 100)); // Output: 80

//===========================
//   FUNCTION COMPOSITION
//===========================
const compose_fc = (...fns) => (x) => fns.reduceRight((acc, fn) => fn(acc), x);

// Example: Double and square
const double = (x) => x * 2;
const square_fc = (x) => x ** 2;

const composed = compose_fc(double, square_fc); // square first, then double
console.log(composed(3)); // (3^2) * 2 = 18


//---------------------------------------------------------------------------------------

//===========================
//  FP Basics
//===========================
// Pure function: depends only on input arguments
const add = (x, y) => x + y;

// Not pure: modifies state outside its scope
let total = 0;
const addToTotal = (x) => {
    total += x; // modifies external state
    return total;
};

console.log(add(2, 3));        // 5
console.log(addToTotal(5));    // 5

// Immutability
const originalArray = [1, 2, 3];
const newArray = [...originalArray, 4]; // Create a new array by copying

console.log(originalArray); // [1, 2, 3]
console.log(newArray);      // [1, 2, 3, 4]

// First Class and Higher Order Functions
const square = (x) => x * x;
const applyFunction = (func, value) => func(value);

console.log(applyFunction(square, 5)); // 25

// Recursion
const factorial = (n) => {
  if (n === 0) return 1;
  return n * factorial(n - 1);
};

console.log(factorial(5)); // 120

// Function Composition
const multiplyByTwo = (x) => x * 2;
const addThree = (x) => x + 3;

const compose = (f, g) => (x) => f(g(x));

const newFunction = compose(multiplyByTwo, addThree);
console.log(newFunction(5)); // (5 + 3) * 2 = 16

// MAP, FILTER, REDUCE - Higher Order Functions
const numbers = [1, 2, 3, 4, 5];

// Imperative approach (how to do it)
const squaredNumbers = [];
for (let num of numbers) {
    squaredNumbers.push(num ** 2);
}

// Declarative approach (what to do)
const squaredNumbersFP = numbers.map((x) => x ** 2);

console.log(squaredNumbers);      // [1, 4, 9, 16, 25]
console.log(squaredNumbersFP);    // [1, 4, 9, 16, 25]
