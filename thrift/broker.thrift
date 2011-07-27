/**
 * thrift interface for the shinken broker.
 * @warning It may change in an imcompatible way before 1.0 shinken release
 *
 * It is heavily based on livestatus API decribed at http://mathias-kettner.de/checkmk_livestatus.html
 * and implemented in the livestatus shinken module. You should refer to it for filters and stats.
 * @see http://mathias-kettner.de/checkmk_livestatus.html
 * @version 0.1
 * @author <nicolas.dupeux@arkea.com>
 */

namespace * org.shinkenmonitoring.broker

/** 
 * List of tables you can query
 */
enum Table {
  hosts = 0,
  services = 1,
  hostgroups = 2,
  servicegroups = 3,
  contacts = 4,
  contactgroups = 5,
  comments = 6,
  downtimes = 7,
  commands = 8,
  timeperiods = 9,
  hostsbygroup = 10,
  servicesbygroup = 11,
  servicebyhostgroup = 12,
  status = 13,
  log = 14,
  schedulers = 15,
  pollers = 16,
  brokers = 17,
  problems = 18,
  columns = 19,
}

/**
 * Characteristics of the query's results
 */
struct OutputRequest {
  /** List of columns to retrieve */
  1: list<string> columns,
  /** Number of elements to retrieve */
  2: i32 limit,
}

/** Query filters. Filters are expressed using LQL filters syntax
 * Filters are anded together. 
 * You can use boolean expression between filters using 'And' and
 * 'Or' operators and the number of filters to combine in reference
 * field.
 */
struct FilterRequest {
  /** Column name */
  1: string attribute,
  /** Operator */
  2: string operator,
  /** Reference value */
  3: string reference,
}
typedef list<FilterRequest> FiltersRequest

/** Stats query */
struct StatRequest {
  /** Column name */
  1: string attribute,
  /** Operator */
  2: string operator,
  /** Reference value */
  3: string reference,
}
typedef list<StatRequest> StatsRequest


/**
 *  Get request
 */
struct GetRequest {
  /** Table to query */
  1: required Table table,
  /** Output modifiers */
  2: OutputRequest output,
  /** Query filters */
  3: FiltersRequest filters,
  /** Stats */
  4: StatsRequest stats,
}

typedef i32 ExceptionCode

exception BrokerException {
  1: ExceptionCode code,
  2: string message,
}

typedef list<string> StringList

/**
 * Response to a get query
 */
struct GetResponse {
  /** Result table. The first record is the columns name. */
  1: list<StringList> result_table,
}

service Broker {
  /** get data from shinken */
  GetResponse get(1: GetRequest request) throws (1: BrokerException ex)
}
