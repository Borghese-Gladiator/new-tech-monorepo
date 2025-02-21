// Mostly CHATGPT generated, but had to adjust stringifying for format I want for GDoc

function scrapeRestaurants() {
  const restaurants = [];

  // Select all restaurant entries
  document.querySelectorAll(".restaurantEntry").forEach((entry) => {
    // Check if lunch is mentioned
    if (!entry.innerHTML.toLowerCase().includes("lunch")) {
      return;
    }

    // Extract restaurant name
    const nameElement = entry.querySelector("h4 a");
    const name = nameElement ? nameElement.textContent.trim() : "Unknown";

    // Extract location
    const locationElement = entry.querySelector("p a[href*='/map/']");
    const location = locationElement
      ? locationElement.textContent.trim()
      : "Unknown";

    // Extract cuisine types
    const cuisineElements = entry.querySelectorAll("h4 a[href*='cuisine']");
    const cuisines = Array.from(cuisineElements).map((el) =>
      el.textContent.trim()
    );

    // Add restaurant data to the list
    restaurants.push({ name, location, cuisines });
  });

  return restaurants;
}

restaurantObjList = scrapeRestaurants();

restaurantStrList = restaurantObjList.reduce((acc, restaurant) => {
  acc.push(
    `${restaurant.name} \n\t- ${restaurant.cuisines.join(", ")} \n\t- (${
      restaurant.location
    })`
  );
  return acc;
}, []);

console.log(restaurantStrList.join("\n"));

// REQUIRED to copy to clipboard in dev console
// https://stackoverflow.com/questions/56306153/domexception-on-calling-navigator-clipboard-readtext
setTimeout(
  async () => await navigator.clipboard.writeText(restaurantStrList.join("\n")),
  3000
);
