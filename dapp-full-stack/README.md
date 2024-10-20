## Created on June 26th, 2022 5:03 PM

# Full Stack DApp
Built full stack DApp with Vite, React, TailwindCSS, Hardhat.js with Solidity

## Resouces
- [https://blog.logrocket.com/full-stack-dapp-tutorial-vite-react-tailwind-css-solidity/](https://blog.logrocket.com/full-stack-dapp-tutorial-vite-react-tailwind-css-solidity/)
  - Missing implementation steps for components
  - Missing steps for bootstrapping smart_contracts folder
  - Screenshot does not show entire directory structure

## Client

#### Bootstrapping
- npm create vite@latest
  - select React for both framework and variant
- npm i
- npm run dev
- npm install -D tailwindcss postcss autoprefixer
- npx tailwindcss init -p
- replaced tailwind.config.js and index.css
- add components
- npm install react-icons ethers

## Server

#### Bootstrapping
- mkdir smart_contracts && cd smart_contracts
- npx hardhat
- npm install --save-dev "hardhat@^2.9.9" "@nomiclabs/hardhat-waffle@^2.0.0" "ethereum-waffle@^3.0.0" "chai@^4.2.0" "@nomiclabs/hardhat-ethers@^2.0.0" "ethers@^5.0.0"
- add Transactions.sol
- add deploy-script.sol

## Deployment
- Signup at [Alchemy](https://www.alchemy.com/)
- Pick Ethereum
- Create your first app
  - My First Team
  - First Alchemy App
  - skip payment
- "Edit App" button
  - change Network to Goerlie (Ropsten, Rinkeby, and Kovan are deprecated. Mainnet is the main Ethereum network and costs actual ether)
  - click "Save" button
- download Metamask from [metamask.io](https://metamask.io/) and create an account
- npm i dotenv
- create .env file
  - add ACCOUNT_PRIVATE_KEY by going to Metamask and clicking Export Private Key
  - add ALCHEMY_PROJECT_ID by going to Alchemy and clicking Copy on API KEY
  - add INFURA_PROJECT_ID by going to Infura and clicking Copy on Project ID
- update hardhat.config.js
	- load dotenv information
		```
		require('dotenv').config()
		const ALCHEMY_GOERLI_URL = `https://eth-goerli.alchemyapi.io/v2/${process.env.ALCHEMY_PROJECT_ID}`;
		const INFURA_ROPSTEN_URL = `https://ropsten.infura.io/v3/${process.env.INFURA_PROJECT_ID}`
		const ACCOUNT_PRIVATE_KEY = `0x${process.env.ACCOUNT_PRIVATE_KEY}` // metamask account #1
		```
	- add goerli and ropsten test networks (& defaultNetwork as goerli)
- get test ether from faucet [https://faucet.goerli.starknet.io/](https://faucet.goerli.starknet.io/)
- run command to deploy contract to goerli - `npx hardhat run scripts/deploy-script.js --network goerli`


#### Optional
- Create Infura project and use Ropsten test network. Save Infura project ID into environment variable in .env


#### Bug Fixing
I got stuck on hardhat.config.js error `Invalid account: #0 for network: goerli - private key too short, expected 32 bytes`
- edit hardhat.config.js
  - add at top - `require('dotenv').config()`
  - add in network (goerli) with Alchemy HTTPS url and process.env to load ALCHEMY_API_KEY
- run deploy command - `npx hardhat run scripts/deploy-script.js --network goerli`
  - BUG FIX - `Invalid account: #0 for network: goerli - private key too short, expected 32 bytes`
  - SOLUTION - I was using the Alchemy private key and not the private key of an Ethereum account (create one with MetaMask from [metamask.io](https://metamask.io/))
		- Alchemy API Key is simply the unique identifier for the project ID inside the URL
		- Infura Project Secret is not used for hardhat.config.js