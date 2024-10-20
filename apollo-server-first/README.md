## Created on June 21st, 2022 9:06 PM

# First Apollo GraphQL
Followed these articles to implement a server and client on Heroku
- Legacy tutorial no longer present - [https://www.apollographql.com/docs/tutorial/introduction.html](https://www.apollographql.com/docs/tutorial/introduction.html)
- Apollo Server - [https://www.apollographql.com/docs/apollo-server/getting-started](https://www.apollographql.com/docs/apollo-server/getting-started)
- Apollo Client - [https://www.apollographql.com/docs/react/](https://www.apollographql.com/docs/react/)
=> next steps - go through full stack tutorial [https://www.apollographql.com/tutorials/fullstack-quickstart/introduction](https://www.apollographql.com/tutorials/fullstack-quickstart/introduction)

## General Notes
Apollo is a platform for building a unified supsergraph using GraphQL. Apollo is meant to handle Authentication, Pagination, State Management
- Apollo Client - state management library to manage both local and remote data with GraphQL (fetch, cache, modify application data)
- Apollo Server - open source GraphQL server compatible with any GraphQL client like Apollo Client and has a self-documenting GraphQL API
- Apollo Studio - cloud-hosted collection of tools to measure graph's performance
- Apollo Federation - divide functionality across multiple GraphQL services into subgraphs and a GraphQL gateway (both the gateway and subgraphs are a GraphQL server).


## Apollo Server
Packages
- apollo-server is the core library for Apollo Server itself, which helps you define the shape of your data and how to fetch it.
- graphql is the library used to build a GraphQL schema and execute queries against it.


GraphQL Server Parts
- Schema - define structure of data that clients can query
- Data set is the actual data in the form of the schema
- Resolver - tell Apollo Server how to fetch data associated with a particular type
- GraphQL supported server like an Instance of ApolloServer


Schema
- `!` means non-nullable
- `[Book]` means list of Books
- Scalar - Int, Float, String, Boolean, ID
- Object - collection of fields (name of type is called __typename and is always a valid query for any GraphQL server - ```query UniversalQuery {__typename}```)
  - Query - special object that defines all top level entry points for queries (read operations)
    ```
    query GetBooks {
      books {
        title
        author {
          name
        }
      }
    }```
  - Mutation - same as Query except for write operations
    ```
    mutation CreateBook {
      addBook(title: "Fox in Socks", author: "Dr. Seuss") {
        title
        author {
          name
        }
      }
    }```
- Input - special type objects to provide hierarchical data as arguments to fields
  - Purpose of Input is to have an Input type for valid inputs for field or directive arguments [https://stackoverflow.com/questions/41743253/whats-the-point-of-input-type-in-graphql](https://stackoverflow.com/questions/41743253/whats-the-point-of-input-type-in-graphql)
- Enum
  ```
  enum AllowedColor {
    RED
    GREEN
    BLUE
  }```
- Union - return any object type that's included in union
  ```
  union Media = Book | Movie
  type Query {
    allMedia: [Media] # This list can include both Book and Movie objects
  }
  ```
  - query for union
    ```
    query GetSearchResults {
      search(contains: "Shakespeare") {
        # Querying for __typename is almost always recommended,
        # but it's even more important when querying a field that
        # might return one of multiple types.
        __typename
        ... on Book {
          title
        }
        ... on Author {
          name
        }
      }
    }```
- Interface - specifies set of fields multiple object types can include
  ```
  interface Book {
    title: String!
    author: Author!
  }
  type Textbook implements Book {
    title: String! # Must be present
    author: Author! # Must be present
    courses: [Course!]!
  }
  ```
  - Field can have an interface as its return type and return any object type that implements that interface
    ```
    type Query {
      books: [Book!] # Can include Textbook objects
    }
    ```

Custom Scalars like dates - [https://www.apollographql.com/docs/apollo-server/schema/custom-scalars](https://www.apollographql.com/docs/apollo-server/schema/custom-scalars)

#### Steps
- `npm init -y`
- `npm i apollo-server graphql`
- `touch index.js`
- write graphql schema
- write data set constants
- write resolver that returns data set
- create instance of ApolloServer
- add start server command
- Execute my first query using Sandbox UI - [https://studio.apollographql.com/sandbox/explorer](https://studio.apollographql.com/sandbox/explorer)
  - Operations panel writes and executes queries
  - Response panel for results
  - Tabs for schema exploration, search, and settings
  - URL bar for connecting to other GraphQL servers in upper left
  - query
    ```
    query GetBooks {
      books {
        title
        author
      }
    }
    ```
- use PORT env in index.js
- created Procfile
- created Heroku app through UI - `apollo-heroku-deployment0791`
- login to Heroku - `heroku login`
- set remote to push to app - `heroku git:remote -a apollo-heroku-deployment0791`
- deploy subtree to Heroku from root - `git subtree push --prefix server heroku master`
  - Reference - [https://jtway.co/deploying-subdirectory-projects-to-heroku-f31ed65f3f2](https://jtway.co/deploying-subdirectory-projects-to-heroku-f31ed65f3f2)
- set heroku app to development - `heroku config:set NODE_ENV=development` => required because "introspection is disabled by default when Apollo Server is in a production environment, which prevents tools like Apollo Sandbox from working."


## Apollo Client
- @apollo/client: This single package contains virtually everything you need to set up Apollo Client. It includes the in-memory cache, local state management, error handling, and a React-based view layer.
- graphql: This package provides logic for parsing GraphQL queries.


Queries - useQuery hook
- write GET using gqp
  ```
  const GET_DOG_PHOTO = gql`
    query Dog($breed: String!) {
      dog(breed: $breed) {
        id
        displayImage
      }
    }
  `;
  ```
- caching
  ```
  const { loading, error, data } = useQuery(GET_DOG_PHOTO, {
    variables: { breed },
  });
  ```
- Updating caching query results
  - Polling - pass pollInterval configuration option to the useQuery hook
  - Refetching - refresh query results in response to a particular user action


Mutations - useMutation hook
- write POST using gql


#### Notes
- `npm install @apollo/client graphql --template typescript`
- initialize ApolloClient inside index.tsx
- Connect your client to React by adding ApolloProvider around App
- Fetch data with useQuery by creating ExchangeRates component
- Add types to ExchangeRates component

## Apollo Custom Fullstack
I wrote this custom to connect the two articles from Apollo Client and Apollo Server


#### Notes
- Updated Apollo Client URL in index.tsx - (natively, it seems to just connect to one server endpoint at a time)

## Next Steps
- Apollo Client with multiple Apollo Server endpoints
	- query third party site
	- query my Heroku site

#### Archive
Legacy Apollo Tutorial content
- Initialization based on [https://github.com/apollographql/fullstack-tutorial](https://github.com/apollographql/fullstack-tutorial)
  - add .gitignore
  - server
    - `npm init -y`
    - download store.sqlite
    - `npm i apollo-datasource apollo-datasource-rest dotenv apollo-server graphql isemail nodemon sequelize sqlite3`
    - `npm i -D apollo apollo-link apollo-link-http jest nock node-fetch`
  - client
    - `npx create-react-app client --template typescript`
