//===========================
//   Monads
//===========================
// manage side effects by structuring computations while maintaining purity

class Maybe {
  constructor(value) {
    this.value = value;
  }

  // Wraps a value into a Maybe instance
  static of(value) {
    return new Maybe(value);
  }

  // Applies a function to the value if it is not null/undefined
  map(fn) {
    if (this.value == null) {
      return Maybe.of(null); // Return a Maybe with null
    }
    return Maybe.of(fn(this.value));
  }

  // Returns the encapsulated value or a default if it's null/undefined
  getOrElse(defaultValue) {
    return this.value == null ? defaultValue : this.value;
  }

  // EXTRA function to handle chaining
  flatMap(fn) {
    if (this.value == null) {
      return Maybe.of(null);
    }
    return fn(this.value); // Avoid wrapping in another Maybe
  }

}

// BASIC USAGE
const parseName = (user) => user.name;
const uppercase = (str) => str.toUpperCase();

const user = { name: "Alice" };
const userWithoutName = {};

const nameMonad = Maybe.of(user)
  .map(parseName) // Extract name
  .map(uppercase); // Uppercase it
console.log(nameMonad.getOrElse("No name")); // Output: "ALICE"

const noNameMonad = Maybe.of(userWithoutName)
  .map(parseName)
  .map(uppercase);
console.log(noNameMonad.getOrElse("No name")); // Output: "No name"

// CHAINING USAGE
const fetchUser = (id) =>
  id === 1
    ? Maybe.of({ name: "Alice" }) // Simulated API response
    : Maybe.of(null);

const userName = fetchUser(1)
  .flatMap((user) => Maybe.of(user.name))
  .map(uppercase);
console.log(userName.getOrElse("User not found")); // Output: "ALICE"

const missingUser = fetchUser(2)
  .flatMap((user) => Maybe.of(user.name))
  .map(uppercase);
console.log(missingUser.getOrElse("User not found")); // Output: "User not found"