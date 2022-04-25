#include <eosiolib/eosio.hpp>
#include <eosiolib/print.hpp>
#include <eosiolib/asset.hpp>

using namespace eosio;

struct transfer_args {
	account_name from;
	account_name to;
	asset quantity;
	std::string memo;
};

class atkforg : public contract {
public:
	using contract::contract;
	[[eosio::action]] void transfer(uint64_t sender, uint64_t receiver) {
		transfer_args t = unpack_action_data<transfer_args>();
		require_recipient(::eosio::string_to_name(t.memo.c_str()));
	}
};

extern "C" { 
	void apply(uint64_t receiver, uint64_t code, uint64_t action) { 
		if((code == receiver && action != ::eosio::string_to_name("transfer"))
		|| (code == N(eosio.token) && action == ::eosio::string_to_name("transfer"))) { 
			atkforg thiscontract(receiver); 
			switch(action) { 
			case ::eosio::string_to_name("transfer"): 
				eosio::execute_action(&thiscontract, &atkforg::transfer); 
				break; 
			}
		} 
	} 
}
