/**
 * This file described the TSCA interface for shinken
 * TSCA stand for Thrift Service Check Acceptor
 * It implement the same interface than NSCA with the following improvements:
 *  - No more limits on plugin output
 *  - multi languages clients
 *  - send severals results at once
 *
 * Support languages are:
 * 	C++, Java, Python, PHP, Ruby, Erlang, Perl, Haskell,
 * 	C#, Cocoa, JavaScript, Node.js, Smalltalk, and OCaml
 *
 * Written by Jean Max Leblanc <jmax.leblanc@gmail.com>
 */

namespace * org.shinken_monitoring.tsca

enum ReturnCode {
  OK = 0,
  WARNING = 1,
  CRITICAL = 2,
  UNKNOWN = 3,
}

struct State {
  1: i64 timestamp,
  2: string hostname,
  3: string serv,
  4: string output,
  5: ReturnCode rc,
}

struct dataReturn{
  1: bool returnVal,
}

struct dataArgs{
  1: list<State> states,
}

service StateService {
 dataReturn submit_list(1: dataArgs arguments),
}
