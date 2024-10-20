import {
  useQuery,
  gql
} from "@apollo/client";

/*
const EXCHANGE_RATES = gql`
  query GetExchangeRates {
    rates(currency: "USD") {
      currency
      rate
    }
  }
`;

type Rate = {
  currency: number,
  rate: number
}
const ExchangeRates: React.FunctionComponent = () => {
  const { loading, error, data } = useQuery(EXCHANGE_RATES);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error :</p>;

  return data.rates.map(({ currency, rate }: Rate) => (
    <div key={currency}>
      <p>
        {currency}: {rate}
      </p>
    </div>
  ));
}
*/

const GET_BOOKS = gql`
  query GetBooks {
		books {
			title,
			author
		}
	}
`;

type Book = {
	title: string,
	author: string
}

const BooksList: React.FunctionComponent = () => {
  const { loading, error, data } = useQuery(GET_BOOKS);
	console.log(data);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error :</p>;
	return (
		<ul>
			{data.books.map(({ title, author }: Book, idx: number) => {
				return (
					<li key={`books-${idx}`}>
						<span>"{title}" - {author}</span>
					</li>
				)
			})}
		</ul>
	)
}

const App: React.FunctionComponent = () => {
  return (
    <div>
			<h2>Books list 🚀</h2>
			<BooksList />
    </div>
  );
}

export default App;
