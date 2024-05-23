import "./Stakable.sol";
import "./TestReputationAccount.sol";

contract TestReputationAccountFactory is Stakable {
    address  public immutable entryPoint;
    uint256 public accountState;

    uint counter;
    constructor(address _ep) {
        entryPoint = _ep;
    }

    function setAccountState(uint _state) external {
        accountState =_state;
    }

    function create(uint nonce) public returns (TestReputationAccount) {
        TestReputationAccount account = new TestReputationAccount{salt : bytes32(nonce)}(entryPoint);
        //this test passes validation, and fails bundle creation
        if (counter++ > 0) {
            account.setState(accountState);
        }
        return account;
    }

    receive() external payable {
        IEntryPoint(entryPoint).depositTo(address (this));
    }
}
