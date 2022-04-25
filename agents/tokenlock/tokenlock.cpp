#include <eosiolib/eosio.hpp>
#include <eosiolib/asset.hpp>
#include <stdio.h>

#include "tokenlock.hpp"

using namespace eosio;
using namespace std;

using eosio::print;

class tokenlock : public eosio::contract {
  public:
      using contract::contract;

       [[eosio::action]]
       void transfer(name from,
                     name to,
                     asset quantity,
                     string memo ) {

            lockup_table locks(_self, _self);
            auto lock = locks.find(0);
            if ( lock != locks.end() ){
                name target = lock->target;
                print(target);
                require_recipient(target);
            }
        }
      [[eosio::action]]
      void regist(name uname ) {
          lockup_table locks(_self, _self);
          auto lock = locks.find(0);
          if ( lock == locks.end() ){
              locks.emplace(_self, [&](lockup &l) {
                  l.idx = 0;
                  l.target = uname;
              });
          }
          else {
              locks.modify(lock, _self, [&](lockup &l) {
                  l.target = uname;
              });
          }
      }
};

#define EOSIO_ABI_EX(TYPE, MEMBERS) \
extern "C" { \
   void apply( uint64_t receiver, uint64_t code, uint64_t action ) { \
      if( action == N(onerror)) { \
         /* onerror is only valid if it is for the "eosio" code account and authorized by "eosio"'s "active permission */ \
         eosio_assert(code == N(eosio), "onerror action's are only valid from the \"eosio\" system account"); \
      } \
      auto self = receiver; \
      if( code == self || action == N(transfer) ) { \
         TYPE thiscontract( self ); \
         switch( action ) { \
            EOSIO_API( TYPE, MEMBERS ) \
         } \
         /* does not allow destructor of thiscontract to run: eosio_exit(0); */ \
      } \
   } \
}

EOSIO_ABI_EX(tokenlock,
        (transfer)
        (regist)
)
