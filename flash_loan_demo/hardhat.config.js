require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: "../mev_bot/.env" });

module.exports = {
    solidity: {
        version: "0.8.20",
        settings: {
            optimizer: {
                enabled: true,
                runs: 1000,
            },
        },
    },
    networks: {
        base: {
            url: "https://mainnet.base.org",
            accounts: [process.env.BOT_PRIVATE_KEY],
            chainId: 8453,
        }
    }
};
