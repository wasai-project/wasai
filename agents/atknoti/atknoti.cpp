#include <eosiolib/eosio.hpp>
#include <eosiolib/print.hpp>
#include <eosiolib/asset.hpp>

using namespace eosio;

class atknoti : public contract {
public:
	using contract::contract;
	[[eosio::action]] void transfer(account_name from, account_name to, asset quantity, std::string memo) {
		if(from == _self) {
			require_recipient(to);
		}
		else {
			action(
				permission_level{_self, N(active)},
				to, 
				N(transfer),
				std::make_tuple(
					N(atknoti), 
					to, 
					quantity, 
					memo
				)
			).send();
		}	
	}
};

EOSIO_ABI(atknoti, (transfer))
