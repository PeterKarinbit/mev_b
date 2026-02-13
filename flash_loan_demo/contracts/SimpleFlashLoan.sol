// SPDX-License-Identifier: MIT
pragma solidity 0.8.10;

import {FlashLoanSimpleReceiverBase} from "@aave/core-v3/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import {IPoolAddressesProvider} from "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import {IERC20} from "@aave/core-v3/contracts/dependencies/openzeppelin/contracts/IERC20.sol";

contract SimpleFlashLoan is FlashLoanSimpleReceiverBase {
    // Event to log the flash loan execution
    event FlashLoanExecuted(address asset, uint256 amount, uint256 premium);

    constructor(address _addressProvider)
        FlashLoanSimpleReceiverBase(IPoolAddressesProvider(_addressProvider))
    {}

    /**
     * @notice This is the function that Aave calls back after transferring the funds.
     * @param asset The address of the flash-borrowed asset
     * @param amount The amount of the flash-borrowed asset
     * @param premium The fee of the flash-borrowed asset
     * @param initiator The address of the flashloan initiator
     * @param params The byte-encoded params passed when initiating the flashloan
     * @return True if the execution of the operation succeeds, false otherwise
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        
        // --- LOGIC START ---
        
        // 1. We just received `amount` of `asset` (e.g. 1,000 DAI).
        // 2. We can now use this money for Arbitrage, Liquidation, etc.
        //    (For this demo, we just print it and return it).
        
        emit FlashLoanExecuted(asset, amount, premium);

        // 3. We must approve the Pool to take back the `amount + premium`.
        uint256 amountOwed = amount + premium;
        IERC20(asset).approve(address(POOL), amountOwed);

        // --- LOGIC END ---

        return true;
    }

    /**
     * @notice Initiates a flash loan.
     * @param _token The address of the token to flash loan (e.g. DAI)
     * @param _amount The amount to flash loan (e.g. 1000 * 10**18)
     */
    function requestFlashLoan(address _token, uint256 _amount) public {
        address receiverAddress = address(this);
        address asset = _token;
        uint256 amount = _amount;
        bytes memory params = "";
        uint16 referralCode = 0;

        POOL.flashLoanSimple(
            receiverAddress,
            asset,
            amount,
            params,
            referralCode
        );
    }
}
