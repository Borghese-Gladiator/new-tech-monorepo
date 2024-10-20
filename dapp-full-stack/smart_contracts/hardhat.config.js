require('dotenv').config()
require("@nomiclabs/hardhat-waffle");

const ALCHEMY_GOERLI_URL = `https://eth-goerli.alchemyapi.io/v2/${process.env.ALCHEMY_PROJECT_ID}`;
const INFURA_ROPSTEN_URL = `https://ropsten.infura.io/v3/${process.env.INFURA_PROJECT_ID}`
const ACCOUNT_PRIVATE_KEY = `0x${process.env.ACCOUNT_PRIVATE_KEY}` // metamask account #1

// This is a sample Hardhat task. To learn how to create your own go to
// https://hardhat.org/guides/create-task.html
task("accounts", "Prints the list of accounts", async (taskArgs, hre) => {
	const accounts = await hre.ethers.getSigners();

	for (const account of accounts) {
		console.log(account.address);
	}
});

// You need to export an object to set up your config
// Go to https://hardhat.org/config/ to learn more

/**
 * @type import('hardhat/config').HardhatUserConfig
 */
module.exports = {
	solidity: "0.8.4",
	defaultNetwork: "goerli",
	networks: {
		hardhat: {
			chainId: 1337
		},
		goerli: {
			url: ALCHEMY_GOERLI_URL,
			accounts: [ACCOUNT_PRIVATE_KEY]
		},
		ropsten: {
			url: INFURA_ROPSTEN_URL,
			accounts: [ACCOUNT_PRIVATE_KEY]
		}
	},
};
