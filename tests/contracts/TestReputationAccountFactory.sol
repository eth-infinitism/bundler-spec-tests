import "./Stakable.sol";
import "./TestReputationAccount.sol";

contract TestReputationAccountFactory is Stakable {
    address  public immutable entryPoint;
    constructor(address _ep) {
        entryPoint = _ep;
    }

    function create(uint nonce) public returns (TestReputationAccount) {
        TestReputationAccount account = new TestReputationAccount{salt : bytes32(nonce)}(entryPoint);
        return account;
    }

    receive() external payable {
        IEntryPoint(entryPoint).depositTo(address (this));
    }
}
