const hre = require("hardhat");

async function main() {
    const [deployer] = await hre.ethers.getSigners();
    const balance = await hre.ethers.provider.getBalance(deployer.address);

    console.log("═".repeat(60));
    console.log("🚀 DEPLOYING FelixFlashArb to Base Mainnet");
    console.log("═".repeat(60));
    console.log(`  Deployer: ${deployer.address}`);
    console.log(`  Balance:  ${hre.ethers.formatEther(balance)} ETH`);

    // Estimate gas cost first
    const feeData = await hre.ethers.provider.getFeeData();
    const gasPrice = feeData.gasPrice;
    console.log(`  Gas price: ${hre.ethers.formatUnits(gasPrice, "gwei")} gwei`);

    // Deploy with optimizer (already enabled in hardhat.config)
    console.log("\n  Compiling & deploying...");
    const Factory = await hre.ethers.getContractFactory("FelixFlashArb");

    // Use minimal gas settings
    const contract = await Factory.deploy();

    await contract.waitForDeployment();
    const addr = await contract.getAddress();

    // Check deployment cost
    const receipt = await contract.deploymentTransaction().wait();
    const gasCost = receipt.gasUsed * receipt.gasPrice;

    console.log("\n" + "═".repeat(60));
    console.log("✅ DEPLOYED SUCCESSFULLY!");
    console.log("═".repeat(60));
    console.log(`  Contract:  ${addr}`);
    console.log(`  Gas used:  ${receipt.gasUsed.toString()}`);
    console.log(`  Gas cost:  ${hre.ethers.formatEther(gasCost)} ETH`);
    console.log(`  Gas cost:  $${(parseFloat(hre.ethers.formatEther(gasCost)) * 2500).toFixed(4)}`);

    // Verify owner
    const owner = await contract.owner();
    console.log(`  Owner:     ${owner}`);

    // Remaining balance
    const newBalance = await hre.ethers.provider.getBalance(deployer.address);
    console.log(`  Remaining: ${hre.ethers.formatEther(newBalance)} ETH`);

    console.log("\n📋 NEXT STEPS:");
    console.log(`  1. Save contract address: ${addr}`);
    console.log(`  2. Update mev_bot/.env with FELIX_ARB_CONTRACT=${addr}`);
    console.log(`  3. Run: python mev_bot/felix_flash_execute.py`);
    console.log("\n⚠️  Contract uses ZERO of your ETH balance for trades!");
    console.log("    It only uses Balancer flash loans (0 fee on Base).");
    console.log("    Your wallet ETH is ONLY consumed as gas.");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
