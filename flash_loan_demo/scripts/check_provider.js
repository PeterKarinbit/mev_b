const { ethers } = require("ethers");

async function check() {
    const provider = new ethers.JsonRpcProvider("https://mainnet.base.org");
    // This is the known Pool address
    const poolAddr = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5";

    const abi = ["function ADDRESSES_PROVIDER() view returns (address)"];
    const pool = new ethers.Contract(poolAddr, abi, provider);

    try {
        const ap = await pool.ADDRESSES_PROVIDER();
        console.log("Found PoolAddressesProvider:", ap);
    } catch (e) {
        console.log("Error:", e.message);
    }
}
check();
