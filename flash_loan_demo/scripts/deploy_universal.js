
const hre = require("hardhat");

async function main() {
    const [deployer] = await hre.ethers.getSigners();
    console.log("🚀 Deploying UniversalDemonArb...");
    const Factory = await hre.ethers.getContractFactory("UniversalDemonArb");
    const contract = await Factory.deploy();
    await contract.waitForDeployment();
    const addr = await contract.getAddress();
    console.log(`✅ UniversalDemonArb deployed to: ${addr}`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
