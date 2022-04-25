#include <eosiolib/eosio.hpp>
#include <eosiolib/print.hpp>
#include <eosiolib/asset.hpp>
#include <eosiolib/transaction.h>

using namespace eosio;

class eosfun : public contract {
public:
	using contract::contract;

	[[eosio::action]] 
	void transfer(
		account_name from,
		account_name to,
		asset quantity,
		std::string memo) {
		if(from == _self || to != _self) return;
		if((tapos_block_prefix() / 75321 + 6984) % 10) {
			action(
				permission_level{_self, N(active)},
				N(eosio.token),
				N(transfer),
				std::make_tuple(
					_self,
					from,
					quantity * 11 / 10,
					memo
				)
			).send();
		}
	}
};

#define EOSIO_ABI_EX( TYPE, MEMBERS ) \
extern "C" { \
   void apply( uint64_t receiver, uint64_t code, uint64_t action ) { \
      auto self = receiver; \
      if( code == N(eosio.token) ) { \
         TYPE thiscontract( self ); \
         switch( action ) { \
            EOSIO_API( TYPE, MEMBERS ) \
         } \
         /* does not allow destructor of thiscontract to run: eosio_exit(0); */ \
      } \
   } \
}

EOSIO_ABI_EX( eosfun, (transfer) )
