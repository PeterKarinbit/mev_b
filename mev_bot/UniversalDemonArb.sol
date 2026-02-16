
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IBalancerVault {
    function flashLoan(address recipient, address[] memory tokens, uint256[] memory amounts, bytes memory userData) external;
}

interface IUniswapV3Router {
    struct ExactInputSingleParams {
        address tokenIn; address tokenOut; uint24 fee; address recipient;
        uint256 deadline; uint256 amountIn; uint256 amountOutMinimum; uint160 sqrtPriceLimitX96;
    }
    function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
}

interface IAerodromeV3Router {
    struct ExactInputSingleParams {
        address tokenIn; address tokenOut; uint24 tickSpacing; address recipient;
        uint256 deadline; uint256 amountIn; uint256 amountOutMinimum; uint160 sqrtPriceLimitX96;
    }
    function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
}

interface IAerodromeV2Router {
    struct Route { address from; address to; bool stable; address factory; }
    function swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, Route[] calldata routes, address to, uint256 deadline) external returns (uint256[] memory amounts);
}

contract UniversalDemonArb {
    address private constant BALANCER_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;
    address private constant WETH           = 0x4200000000000000000000000000000000000006;
    address public immutable owner;

    struct ArbConfig {
        address targetToken;
        address uniRouter;   // router for DEX 1
        address aeroRouter;  // router for DEX 2
        address aeroFactory; // only for V2
        uint24 uniFee;
        uint24 aeroFeeOrTS;  // fee for V3, tickSpacing for Slipstream
        uint8 mode;          // 1: Aero->Uni, 2: Uni->Aero
        uint8 aeroType;      // 0: AeroV2, 1: UniV3/PancakeV3, 2: AeroSlipstream
    }

    constructor() { owner = msg.sender; }

    function execute(uint256 amount, ArbConfig calldata config) external {
        require(msg.sender == owner, "!owner");
        address[] memory tokens = new address[](1);
        tokens[0] = WETH;
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        IBalancerVault(BALANCER_VAULT).flashLoan(address(this), tokens, amounts, abi.encode(config));
    }

    function receiveFlashLoan(address[] memory, uint256[] memory amounts, uint256[] memory, bytes memory userData) external {
        require(msg.sender == BALANCER_VAULT, "!vault");
        ArbConfig memory c = abi.decode(userData, (ArbConfig));
        uint256 loan = amounts[0];
        uint256 bal = loan;

        if (c.mode == 1) { // DEX 2 -> DEX 1
            bal = _swapOut(bal, c.aeroRouter, WETH, c.targetToken, c.aeroFeeOrTS, c.aeroType, c.aeroFactory);
            bal = _swapOut(bal, c.uniRouter, c.targetToken, WETH, c.uniFee, 1, address(0));
        } else { // DEX 1 -> DEX 2
            bal = _swapOut(bal, c.uniRouter, WETH, c.targetToken, c.uniFee, 1, address(0));
            bal = _swapOut(bal, c.aeroRouter, c.targetToken, WETH, c.aeroFeeOrTS, c.aeroType, c.aeroFactory);
        }

        require(bal >= loan, "!profit");
        IERC20(WETH).transfer(BALANCER_VAULT, loan);
        uint256 p = IERC20(WETH).balanceOf(address(this));
        if (p > 0) IERC20(WETH).transfer(owner, p);
    }

    function _swapOut(uint256 amountIn, address router, address tokenIn, address tokenOut, uint24 feeOrTS, uint8 dexType, address factory) internal returns (uint256) {
        IERC20(tokenIn).approve(router, amountIn);
        if (dexType == 0) { // Aero V2
            IAerodromeV2Router.Route[] memory r = new IAerodromeV2Router.Route[](1);
            r[0] = IAerodromeV2Router.Route(tokenIn, tokenOut, false, factory);
            uint256[] memory res = IAerodromeV2Router(router).swapExactTokensForTokens(amountIn, 0, r, address(this), block.timestamp);
            return res[res.length - 1];
        } else if (dexType == 1) { // UniV3 / PancakeV3
            return IUniswapV3Router(router).exactInputSingle(IUniswapV3Router.ExactInputSingleParams(tokenIn, tokenOut, feeOrTS, address(this), block.timestamp, amountIn, 0, 0));
        } else { // Aero Slipstream
            return IAerodromeV3Router(router).exactInputSingle(IAerodromeV3Router.ExactInputSingleParams(tokenIn, tokenOut, feeOrTS, address(this), block.timestamp, amountIn, 0, 0));
        }
    }
}
