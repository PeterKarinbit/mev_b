// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {FlashLoanSimpleReceiverBase} from "@aave/core-v3/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import {IPoolAddressesProvider} from "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import {IERC20} from "@aave/core-v3/contracts/dependencies/openzeppelin/contracts/IERC20.sol";

interface IRouter {
    struct Route { address from; address to; bool stable; }
    function swapExactTokensForTokens(uint aIn, uint aOut, Route[] calldata r, address to, uint dl) external returns (uint[] memory);
}

interface IUni {
    struct Params { address tokenIn; address tokenOut; uint24 fee; address recipient; uint256 deadline; uint256 amountIn; uint256 amountOutMinimum; uint160 sqrtPriceLimitX96; }
    function exactInputSingle(Params calldata params) external returns (uint256);
}

contract FlashArb is FlashLoanSimpleReceiverBase {
    address public owner;
    address public constant AERO = 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43;
    address public constant UNI = 0x2626664c2603336E57B271c5C0b26F421741e481;

    constructor() FlashLoanSimpleReceiverBase(IPoolAddressesProvider(0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D)) {
        owner = msg.sender;
    }

    function execute(address asset, uint256 amount, bytes calldata params) external {
        require(msg.sender == owner, "!");
        POOL.flashLoanSimple(address(this), asset, amount, params, 0);
    }

    function executeOperation(address asset, uint256 amount, uint256 premium, address, bytes calldata params) external override returns (bool) {
        (bool isLiq, address tB, uint24 fee, bool buyAero, address victim) = abi.decode(params, (bool, address, uint24, bool, address));
        
        if (isLiq) {
            IERC20(asset).approve(address(POOL), amount);
            POOL.liquidationCall(tB, asset, victim, amount, false);
            uint256 bB = IERC20(tB).balanceOf(address(this));
            _swap(tB, asset, bB, fee, true);
        } else {
            if (buyAero) {
                _swap(asset, tB, amount, fee, true);
                _swap(tB, asset, IERC20(tB).balanceOf(address(this)), fee, false);
            } else {
                _swap(asset, tB, amount, fee, false);
                _swap(tB, asset, IERC20(tB).balanceOf(address(this)), fee, true);
            }
        }

        uint256 owed = amount + premium;
        require(IERC20(asset).balanceOf(address(this)) >= owed, "P");
        IERC20(asset).approve(address(POOL), owed);
        
        uint256 p = IERC20(asset).balanceOf(address(this)) - owed;
        if (p > 0) IERC20(asset).transfer(owner, p);
        return true;
    }

    function _swap(address f, address t, uint256 a, uint24 fee, bool aero) internal {
        if (aero) {
            IERC20(f).approve(AERO, a);
            IRouter.Route[] memory r = new IRouter.Route[](1);
            r[0] = IRouter.Route(f, t, false);
            IRouter(AERO).swapExactTokensForTokens(a, 0, r, address(this), block.timestamp);
        } else {
            IERC20(f).approve(UNI, a);
            IUni(UNI).exactInputSingle(IUni.Params(f, t, fee, address(this), block.timestamp, a, 0, 0));
        }
    }

    function withdraw(address t) external {
        if(msg.sender == owner) IERC20(t).transfer(owner, IERC20(t).balanceOf(address(this)));
    }
}
