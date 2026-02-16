
const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    const [deployer] = await hre.ethers.getSigners();
    console.log("🚀 Deploying MclawTriangle...");

    // Copy MclawTriangle.sol to contracts folder if not there
    const srcPath = path.join(__dirname, "../../mev_bot/MclawTriangle.sol");
    const destPath = path.join(__dirname, "../contracts/MclawTriangle.sol");
    if (fs.existsSync(srcPath)) {
        fs.copyFileSync(srcPath, destPath);
    }

    const Factory = await hre.ethers.getContractFactory("MclawTriangle");
    const contract = await Factory.deploy();
    await contract.waitForDeployment();

    const addr = await contract.getAddress();
    console.log(`✅ MclawTriangle deployed to: ${addr}`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
