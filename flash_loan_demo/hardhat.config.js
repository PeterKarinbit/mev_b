require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: "../mev_bot/.env" });

module.exports = {
    solidity: {
        compilers: [
            { version: "0.8.10" },
            { version: "0.8.20" }
        ]
    },
    networks: {
        hardhat: {
            forking: {
                url: "https://mainnet.base.org",
            }
        },
        base: {
            url: "https://mainnet.base.org",
            accounts: [process.env.BOT_PRIVATE_KEY],
            chainId: 8453,
            gasPrice: "auto"
        }
    }
};
