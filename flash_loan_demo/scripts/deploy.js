const hre = require("hardhat");

async function main() {
    console.log("Deploying FlashArb to Base Mainnet...");

    const FlashArb = await hre.ethers.getContractFactory("FlashArb");
    const flashArb = await FlashArb.deploy();
    await flashArb.waitForDeployment();

    const addr = await flashArb.getAddress();
    console.log(`\n✅ FlashArb deployed at: ${addr}`);
    console.log(`\nSave this address! Your bot needs it to trigger trades.`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
