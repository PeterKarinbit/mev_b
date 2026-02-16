
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IBalancerVault {
    function flashLoan(address recipient, address[] memory tokens, uint256[] memory amounts, bytes memory userData) external;
}

interface ISwapRouter {
    struct ExactInputSingleParams { address tokenIn; address tokenOut; uint24 fee; address recipient; uint256 deadline; uint256 amountIn; uint256 amountOutMinimum; uint160 sqrtPriceLimitX96; }
    function exactInputSingle(ExactInputSingleParams calldata params) external returns (uint256);
}

interface IAerodromeRouter {
    struct Route { address from; address to; bool stable; address factory; }
    function swapExactTokensForTokens(uint256 amountIn, uint256 outMin, Route[] calldata routes, address to, uint256 deadline) external returns (uint256[] memory);
}

contract FlashArbV2 {
    address private constant BALANCER_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;
    address private constant WETH           = 0x4200000000000000000000000000000000000006;
    address private constant USDC           = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;

    address public immutable owner;
    constructor() { owner = msg.sender; }

    struct ArbConfig {
        address targetToken;
        address uniRouter;
        address aeroRouter;
        address aeroFactory;
        uint24 uniFee;
        uint8 mode; // 1: Aero->Uni, 2: Uni->Aero
        bool useUsdcHop;
    }

    function execute(uint256 amount, ArbConfig calldata config) external {
        require(msg.sender == owner, "!owner");
        address[] memory tokens = new address[](1);
        tokens[0] = WETH;
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        IBalancerVault(BALANCER_VAULT).flashLoan(address(this), tokens, amounts, abi.encode(config));
    }

    function receiveFlashLoan(address[] memory, uint256[] memory amounts, uint256[] memory, bytes memory userData) external {
        ArbConfig memory c = abi.decode(userData, (ArbConfig));
        uint256 loan = amounts[0];
        uint256 bal = loan;

        if (c.mode == 1) { // Aero -> Uni
            bal = _swapAeroWethToToken(bal, c);
            bal = _swapUniTokenToWeth(bal, c);
        } else { // Uni -> Aero
            bal = _swapUniWethToToken(bal, c);
            bal = _swapAeroTokenToWeth(bal, c);
        }

        require(bal >= loan, "!profit");
        IERC20(WETH).transfer(BALANCER_VAULT, loan);
    }

    function _swapAeroWethToToken(uint256 amt, ArbConfig memory c) internal returns (uint256) {
        IERC20(WETH).approve(c.aeroRouter, amt);
        if (c.useUsdcHop) {
            IAerodromeRouter.Route[] memory r = new IAerodromeRouter.Route[](2);
            r[0] = IAerodromeRouter.Route(WETH, USDC, false, c.aeroFactory);
            r[1] = IAerodromeRouter.Route(USDC, c.targetToken, false, c.aeroFactory);
            uint256[] memory res = IAerodromeRouter(c.aeroRouter).swapExactTokensForTokens(amt, 0, r, address(this), block.timestamp);
            return res[res.length - 1];
        } else {
            IAerodromeRouter.Route[] memory r = new IAerodromeRouter.Route[](1);
            r[0] = IAerodromeRouter.Route(WETH, c.targetToken, false, c.aeroFactory);
            uint256[] memory res = IAerodromeRouter(c.aeroRouter).swapExactTokensForTokens(amt, 0, r, address(this), block.timestamp);
            return res[res.length - 1];
        }
    }

    function _swapAeroTokenToWeth(uint256 amt, ArbConfig memory c) internal returns (uint256) {
        IERC20(c.targetToken).approve(c.aeroRouter, amt);
        if (c.useUsdcHop) {
            IAerodromeRouter.Route[] memory r = new IAerodromeRouter.Route[](2);
            r[0] = IAerodromeRouter.Route(c.targetToken, USDC, false, c.aeroFactory);
            r[1] = IAerodromeRouter.Route(USDC, WETH, false, c.aeroFactory);
            uint256[] memory res = IAerodromeRouter(c.aeroRouter).swapExactTokensForTokens(amt, 0, r, address(this), block.timestamp);
            return res[res.length - 1];
        } else {
            IAerodromeRouter.Route[] memory r = new IAerodromeRouter.Route[](1);
            r[0] = IAerodromeRouter.Route(c.targetToken, WETH, false, c.aeroFactory);
            uint256[] memory res = IAerodromeRouter(c.aeroRouter).swapExactTokensForTokens(amt, 0, r, address(this), block.timestamp);
            return res[res.length - 1];
        }
    }

    function _swapUniWethToToken(uint256 amt, ArbConfig memory c) internal returns (uint256) {
        IERC20(WETH).approve(c.uniRouter, amt);
        return ISwapRouter(c.uniRouter).exactInputSingle(ISwapRouter.ExactInputSingleParams(WETH, c.targetToken, c.uniFee, address(this), block.timestamp, amt, 0, 0));
    }

    function _swapUniTokenToWeth(uint256 amt, ArbConfig memory c) internal returns (uint256) {
        IERC20(c.targetToken).approve(c.uniRouter, amt);
        return ISwapRouter(c.uniRouter).exactInputSingle(ISwapRouter.ExactInputSingleParams(c.targetToken, WETH, c.uniFee, address(this), block.timestamp, amt, 0, 0));
    }

    function withdraw(address t) external { IERC20(t).transfer(owner, IERC20(t).balanceOf(address(this))); }
}
