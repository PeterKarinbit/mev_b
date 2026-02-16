
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

contract FelixFlashArb {
    address private constant BALANCER_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;
    address private constant WETH           = 0x4200000000000000000000000000000000000006;
    address private constant FELIX          = 0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07;
    address private constant USDC           = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;

    address public immutable owner;
    constructor() { owner = msg.sender; }

    struct ArbConfig {
        address uniRouter;
        address aeroRouter;
        address aeroFactory;
        uint24 uniFee;
        uint8 mode; // 1: Aero->Uni, 2: Uni->Aero
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
            bal = _swapAeroWethToFelix(bal, c.aeroRouter, c.aeroFactory);
            bal = _swapUniFelixToWeth(bal, c.uniRouter, c.uniFee);
        } else { // Uni -> Aero
            bal = _swapUniWethToFelix(bal, c.uniRouter, c.uniFee);
            bal = _swapAeroFelixToWeth(bal, c.aeroRouter, c.aeroFactory);
        }

        require(bal >= loan, "!profit");
        IERC20(WETH).transfer(BALANCER_VAULT, loan);
    }

    function _swapAeroWethToFelix(uint256 amt, address router, address factory) internal returns (uint256) {
        IERC20(WETH).approve(router, amt);
        IAerodromeRouter.Route[] memory r = new IAerodromeRouter.Route[](2);
        r[0] = IAerodromeRouter.Route(WETH, USDC, false, factory);
        r[1] = IAerodromeRouter.Route(USDC, FELIX, false, factory);
        uint256[] memory res = IAerodromeRouter(router).swapExactTokensForTokens(amt, 0, r, address(this), block.timestamp);
        return res[res.length - 1];
    }

    function _swapAeroFelixToWeth(uint256 amt, address router, address factory) internal returns (uint256) {
        IERC20(FELIX).approve(router, amt);
        IAerodromeRouter.Route[] memory r = new IAerodromeRouter.Route[](2);
        r[0] = IAerodromeRouter.Route(FELIX, USDC, false, factory);
        r[1] = IAerodromeRouter.Route(USDC, WETH, false, factory);
        uint256[] memory res = IAerodromeRouter(router).swapExactTokensForTokens(amt, 0, r, address(this), block.timestamp);
        return res[res.length - 1];
    }

    function _swapUniWethToFelix(uint256 amt, address router, uint24 fee) internal returns (uint256) {
        IERC20(WETH).approve(router, amt);
        return ISwapRouter(router).exactInputSingle(ISwapRouter.ExactInputSingleParams(WETH, FELIX, fee, address(this), block.timestamp, amt, 0, 0));
    }

    function _swapUniFelixToWeth(uint256 amt, address router, uint24 fee) internal returns (uint256) {
        IERC20(FELIX).approve(router, amt);
        return ISwapRouter(router).exactInputSingle(ISwapRouter.ExactInputSingleParams(FELIX, WETH, fee, address(this), block.timestamp, amt, 0, 0));
    }

    function withdraw(address t) external { IERC20(t).transfer(owner, IERC20(t).balanceOf(address(this))); }
}
