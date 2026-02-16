
const hre = require("hardhat");

async function main() {
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying FlashArbV2 with account:", deployer.address);

    const FlashArb = await hre.ethers.getContractFactory("FlashArbV2");
    const contract = await FlashArb.deploy();

    await contract.waitForDeployment();
    const address = await contract.getAddress();

    console.log("FlashArbV2 deployed to:", address);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
