const hre = require("hardhat");

async function main() {
    const [deployer] = await hre.ethers.getSigners();

    // Aave V3 Pool Addresses Provider on BASE MAINNET
    const AAVE_POOL_ADDRESS_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb";

    // Tokens on Base
    const WETH_ADDRESS = "0x4200000000000000000000000000000000000006";
    const USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";

    // Large USDC holder on Base (Coinbase Operating Wallet)
    const USDC_WHALE = "0x3304E22DDaa22bCcC3caA16094A62655bc81823f";

    console.log("--- BASE NETWORK MEV EXECUTION SIMULATOR ---");
    console.log("Deploying Flash Loan Contract to Base Fork...");

    const FlashLoan = await hre.ethers.getContractFactory("SimpleFlashLoan");
    const flashLoan = await FlashLoan.deploy(AAVE_POOL_ADDRESS_PROVIDER);
    await flashLoan.waitForDeployment();

    const contractAddress = await flashLoan.getAddress();
    console.log("Bot Contract Deployed at:", contractAddress);

    // --- FUNDING FOR THE LOAN FEE (0.05% on some LPs, 0.09% on others) ---
    console.log("Impersonating USDC Whale to fund gas/fees...");
    await hre.network.provider.request({
        method: "hardhat_impersonateAccount",
        params: [USDC_WHALE],
    });

    // Fund the whale with ETH for gas
    await hre.network.provider.send("hardhat_setBalance", [
        USDC_WHALE,
        "0xDE0B6B3A7640000", // 1 ETH
    ]);

    const whaleSigner = await hre.ethers.getSigner(USDC_WHALE);
    const usdc = await hre.ethers.getContractAt("IERC20", USDC_ADDRESS);

    // Transfer 10 USDC to contract to cover flash loan premiums
    await usdc.connect(whaleSigner).transfer(contractAddress, hre.ethers.parseUnits("10", 6));
    console.log("Contract funded with 10 USDC for fees.");

    // --- EXECUTE ARBITRAGE ATTACK ---
    const borrowAmount = hre.ethers.parseUnits("5000", 6); // Borrow 5,000 USDC
    console.log(`ATTACK INITIATED: Borrowing ${hre.ethers.formatUnits(borrowAmount, 6)} USDC...`);

    const tx = await flashLoan.requestFlashLoan(USDC_ADDRESS, borrowAmount);
    const receipt = await tx.wait();

    console.log("--- ATTACK COMPLETE ---");
    console.log("Flash Loan successful in one block.");
    console.log("Real World Potential:");
    console.log("  Borrowed: 5,000 USDC");
    console.log("  Gas Cost: ~$0.05 (on Base)");
    console.log("  Payout: Automatic to contract.");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
