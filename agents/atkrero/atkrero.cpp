#include <eosiolib/eosio.hpp>
#include <eosiolib/print.hpp>
#include <eosiolib/asset.hpp>

using namespace eosio;

class atkrero : public contract {
public:
	using contract::contract;

	[[eosio::action]] void g(uint64_t val) {
		action(
			permission_level{_self, N(active)},
			N(reroll), 
			N(upsert),
			std::make_tuple(
				N(atkrero), 
				456UL
			)
		).send();
	}

	[[eosio::action]] void f(uint64_t val) {
		print("atkrero::f, val=");
		print(val);
		print(" --- ");
		if(val == 5) eosio_assert(false, "atkrero::f::eosio_assert: val");
	}
};

EOSIO_ABI(atkrero, (g)(f))
