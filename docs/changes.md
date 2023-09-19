adding a parameter --mas-instance-ids to the must-gather command to specify one or more instances to collect data from.
when specified this only data from these instance will be collected along with data for Mongo and the cluster data.

this is to avoid collecting instance details for different customers in case of multi tennant environment.

when specified, only data from this/these instance(s) will be collected along with data for Mongo and the cluster data.