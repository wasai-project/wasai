/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#include <eosiolib/eosio.hpp>
// #include <eosiolib/symbol.hpp>

using namespace eosio;

struct lockup {
    uint64_t idx;
    name target;

    uint64_t primary_key() const { return idx; }

    EOSLIB_SERIALIZE(lockup, (idx)(target))
};

typedef multi_index<N(lockup), lockup> lockup_table;
