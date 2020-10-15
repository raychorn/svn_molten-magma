require 'rubygems'
ActiveRecord::Base.pluralize_table_names=false

# The walker log file
SALESFORCE_LOGGER = Logger.new("#{RAILS_ROOT}/log/salesforce_walker.log")

class SalesforceWalker < ActiveRecord::Schema
  
  @@logger = SALESFORCE_LOGGER
  
  # Find uses a Paginator because we could be retrieving a large number of 
  # classes.
  # TODO: Should we just retrieve ids instead of all columns?
  PAGE_SIZE = 50  
  
  # Walks through the entire local MySQL database (by default), 
  # deleting records that no longer exist in Salesforce. 
  #
  # Accepts an options hash:
  #
  #   - classes: Will only look for deleted records in the specified
  #              Salesforce classes (Account, Case, etc.)
  #   - time: accepts either a 2 element array (start and end time) or 
  #           1 Time object. If 1 time object is provided, will look for all
  #           local records from that to the current time.
  #   - dry_run: If true, doesn't actually delete the records. Default is false.
  #
  # Uses the paginating find plugin so not all of the records are loaded at once.
  #
  # Example calls: 
  #
  # SalesforceWalker.expire_deleted  => Looks through all local records for all Salesforce
  # Classes.
  #
  # SalesforceWalker.expire_deleted(:classes => [Account,Case]) => Limits the search to the 
  # Account and Case classes. 
  #
  # SalesforceWalker.expire_deleted(:classes => [Solution], :time => 12.days.ago)
  # => Looks for deleted Solution records from 12 days ago until now.
  #
  # SalesforceWalker.expire_deleted(:classes => [Solution], :time => [12.days.ago, 5.days.ago])
  # => Looks for deleted Solution records from 12 days ago until 5 days ago.
  def self.expire_deleted(options = {})
    @@logger.info("[#{Time.now}] Expiring Deleted Records...")
    
    options,classes_hash = set_options_and_classes_hash(options)
    
    @@logger.info("Expiring Deleted Records for the following classes: #{classes_hash.keys.join(', ')}")
    
    classes_hash.each do |salesforce_class, local_class|
      conditions = build_conditions(local_class,options)
      total = local_class.count(:conditions => conditions) 
      @@logger.info("#{total} #{local_class} records")
      records = local_class.find(:all,:limit => PAGE_SIZE,:conditions => conditions)
      i = 0
      count = 0
      while count <= total do
        records.each do |local_record|
          unless salesforce_class.find_by_id(local_record.sf_id)
            @@logger.info("Deleting #{local_class} / #{local_record.sf_id}")
            if options[:dry_run]
              @@logger.info("Dry run...not deleting record")
            else
              local_record.destroy
            end # options[:dry_run]
          end # salesforce_class.find_by_id
          count += 1
          i += 1
          @@logger.info("Record #{count} of #{total} / #{i} of #{PAGE_SIZE}")
        end # records.each
        if count < total
          records = local_class.find(:all,:limit => PAGE_SIZE,:conditions => conditions,:offset => count)
          i = 0
          @@logger.info("Incremented window")
        end
      end
    end # classes_hash.each
    @@logger.info("[#{Time.now}] Done Deleting Expired Records...")
  end
  
  def self.update(options = {})
    @@logger.info("[#{Time.now}] Updating Existing Records...")
    
    options,classes_hash = set_options_and_classes_hash(options)
    
    @@logger.info("Updating Existing Records for the following classes: #{classes_hash.keys.join(', ')}")
    
    classes_hash.each do |salesforce_class, local_class|
      conditions = build_conditions(local_class,options)
      total = local_class.count(:conditions => conditions) 
      @@logger.info("#{total} #{local_class} records")
      records = local_class.find(:all,:limit => PAGE_SIZE,:conditions => conditions)
      i = 0
      count = 0
      while count <= total do
        records.each do |local_record|
          if sf_record = salesforce_class.find_by_id(local_record.sf_id)
            @@logger.info("Updating #{local_class} / #{local_record.sf_id}")
            if options[:dry_run]
              @@logger.info("Dry run...not updating record")
            else
              SalesforceSync.update_record(sf_record,local_record,salesforce_class,local_class)
            end # options[:dry_run]
          end # salesforce_class.find_by_id
          count += 1
          i += 1
          @@logger.info("Record #{count} of #{total} / #{i} of #{PAGE_SIZE}")
        end # records.each
        if count < total
          records = local_class.find(:all,:limit => PAGE_SIZE,:conditions => conditions,:offset => count)
          if records.empty?
            @@logger.info("No records in new window - exiting...")
            break
          end
          i = 0
          @@logger.info("Incremented window")
        end
      end
    end # classes_hash.each
    @@logger.info("[#{Time.now}] Done Updating Records...")
  end
  
  # Walks the Salesforce database, default from one month ago, inserting records that
  # don't exist in the local database. 
  #
  # Accepts an options hash:
  #
  #   - classes: Will only walk thru the specified Salesforce classes in the specified
  #              Salesforce classes (Account, Case, etc.)
  #   - time: Defaults to find all records from one month till now. Accepts either a 2 
  #           element array (start and end time) or 1 Time object. If 1 time object is 
  #           provided, will look for all local records from that to the current time.
  #   - dry_run: If true, doesn't actually delete the records. Default is false.
  #
  # Uses the paginating find plugin so not all of the records are loaded at once.
  #
  # TODO: Time option is NOT WORKING:
  # ActiveRecord::StatementInvalid: ActiveSalesforce::ASFError: INVALID_FIELD: 
  # SELECT id FROM Solution WHERE (last_modified_date < 2006-12-15T08:49:31Z
  #                                ^
  # ERROR at Row:1:Column:32
  # No such column 'last_modified_date' on entity 'Solution'. If you are attempting to use a 
  # custom field, be sure to append the '__c' after the custom field name. Please reference 
  # your WSDL or the describe call for the appropriate names.: SELECT count(*) AS count_all FROM solution 
  # WHERE (last_modified_date < 2006-12-15T08:49:31Z AND last_modified_date > 2006-09-16T08:49:31Z) 
  # 
  def self.insert_new(options = {})
    @@logger.info("[#{Time.now}] Inserting Records from Salesforce into local db...")
    
    options,classes_hash = set_options_and_classes_hash(options)
    
    @@logger.info("Inserting Records for the following classes: #{classes_hash.keys.join(', ')}")
    
    classes_hash.each do |salesforce_class, local_class|
      salesforce_record_paginator = build_paginator(salesforce_class,options) 
      
      # try to find a local record...if it doesn't exist, create one.
      salesforce_record_paginator.each do |salesforce_record|
        unless local_class.find_by_sf_id(salesforce_record.id)
          @@logger.info("Inserting #{local_class} / #{salesforce_record.id}")
          if options[:dry_run]
            @@logger.info("Dry run...not inserting record")
          else
            SalesforceSync.insert_record(salesforce_class.column_names,salesforce_record,salesforce_class,local_class)
          end # options[:dry_run]
        end # salesforce_class.find_by_id
      end # local_record_paginator
    end # classes_hash.each
    @@logger.info("[#{Time.now}] Done Inserting Records...")
  end
  
  private
  
  def self.set_options_and_classes_hash(options)
    options = {:classes => AppConstants::CLASS_MAPPINGS.keys,
               :time => nil, :dry_run => false}.merge!(options)
    
    # Creates Salesforce Class => Local Class hash
    classes_hash = {}
    options[:classes].each do |salesforce_class|
      classes_hash.merge!({salesforce_class => AppConstants::CLASS_MAPPINGS[salesforce_class.to_s ].constantize})
    end
    [options,classes_hash]
  end
  
  def self.build_conditions(klass,options)
    @@logger.info("Finding all #{klass.to_s.pluralize}...")
    if time_range = options[:time]
                                conditions = if time_range.is_a?(Array)
                                                [
                                                 "#{SalesforceSync.set_order_column(klass)} < ? AND #{SalesforceSync.set_order_column(klass)} > ?",
                                                 time_range.last.utc, time_range.first.utc
                                                ]
                                             else
                                                if klass.ancestors.include? SalesforceRecord
                                                  "#{SalesforceSync.set_order_column(klass)} < #{Time.now.utc.strftime("%Y-%m-%dT%H:%M:%SZ")} AND #{SalesforceSync.set_order_column(klass)} > #{time_range.utc.strftime("%Y-%m-%dT%H:%M:%SZ")}"
                                                else
                                                [
                                                 "#{SalesforceSync.set_order_column(klass)} < ? AND #{SalesforceSync.set_order_column(klass)} > ?",
                                                 Time.now.utc, time_range.utc
                                                ]
                                                end
                                             end                                 
                                
    else
      nil
    end
  end
end