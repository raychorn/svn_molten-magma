require("builder")
require("net/http")
require("uri")

# Searchable backend that uses SOLR for index management.
module MojoDNA::Searchable::Solr
  # An indexer using SOLR's web service
  class Indexer
    # set the default analyzer for Searchable
    def self.default_analyzer(analyzer = nil)
      logger.debug("default_analyzer not supported by SOLR backend")
    end
    
    # set the default index path for Searchable
    def self.default_index_path(path = nil)
      logger.debug("default_index_path not supported by SOLR backend")
    end
    
    def self.optimize_index
      http = Net::HTTP.new("localhost", 8983)

      # trigger a SOLR optimize
      http.post('/solr/update', '<optimize/>')
    end
    
    def self.delete_from_index( object )
      field = "_type-id"
      key = "#{object.class.to_s}-#{object.send(:id)}"

      http = Net::HTTP.new("localhost", 8983)
      http.post('/solr/update', "<delete><id>#{key}</id></delete><commit/>")
    end
    
    def self.index( object )
      # create an xml doc representation and send to SOLR
      doc = ""
      xml = Builder::XmlMarkup.new(:target => doc, :indent => 2)
      xml.add do
        xml << create_document( object )
      end

      http = Net::HTTP.new("localhost", 8983)

      # send document to SOLR
      http.post('/solr/update', doc)
      http.post('/solr/update', "<commit/>")
    end
    
    def self.index_all(klass)
      index_created = Time.now
      
      offset = 0
      quanta = 500
      include_ary = []
      http = Net::HTTP.new("localhost", 8983)
      
      begin
        include_ary = klass.searchable_fields.values.collect{|f| f.attr_name unless f.include.empty? or klass.reflections[f.attr_name.to_sym].nil?}.reject{|v| v.nil?}
      rescue NoMethodError
        # Rails 1.0 doesn't have klass.reflections, so assume everything is an association and not a method
        include_ary = klass.searchable_fields.values.collect{|f| f.attr_name unless f.include.empty?}.reject{|v| v.nil?}
      end
      
      # load the first set of objects
      while objects = klass.find(:all, :conditions => ["#{klass.table_name}.id > ?", offset], :limit => quanta, :include => include_ary) do
        break if objects.empty?

        # create an XML doc containing all docs in this batch
        doc = ""
        xml = Builder::XmlMarkup.new(:target => doc, :indent => 2)
        xml.add do
          objects.each do |obj|
            xml << create_document( obj )
          end
        end
        
        # send document to SOLR
        http.post('/solr/update', doc)
        http.post('/solr/update', "<commit/>")

        puts "#{Time.now}: Adding documents to index"
        puts "#{Time.now}: (#{offset})"
        
        # set the offset for the next batch
        offset = objects.last.id
        
        puts "#{Time.now}: Querying for objects"
        objects = klass.find(:all, :conditions => ["#{klass.table_name}.id > ?", offset], :limit => quanta, :include => include_ary)
      end


      # index stuff that was updated since index_created (if we can figure out what it is)
      if klass.column_names.include?("updated_at")
        while objects = klass.find(:all, :conditions => ["#{klass.table_name}.updated_at > ?", index_created], :include => include_ary) do
          break if objects.empty?
          
          # update index_created for the next run
          index_created = Time.now
          
          # TODO create an XML doc containing all docs in this batch
          doc = ""
          xml = Builder::XmlMarkup.new(:target => doc, :indent => 2)
          xml.add do
            objects.each do |obj|
              xml << create_document( obj )
            end
          end
          
          # send document to SOLR
          http.post('/solr/update', doc)
          http.post('/solr/update', "<commit/>")
        end
      end

      # optimize the index
      http.post('/solr/update', '<optimize/>')
      
      puts "#{Time.now}: Done."
    end
    
    def self.create_document(object)
      id = object.send(:id).to_s
      klass = object.class.to_s
      
      doc = ""
      xml = Builder::XmlMarkup.new(:target => doc, :indent => 2)
      xml.doc do
        
        if object.class.searchable_fields or object.respond_to?(:to_doc)
          xml.field(id, :name => "_id" )
          xml.field(klass, :name => "_type" )
          xml.field("#{klass}-#{id}", :name => "_type-id")
        
          object.class.searchable_fields.values.each do |field|
            make_fields( xml, object.send( field.attr_name ), field )
          end
        
          # check to make sure this is a StringIO
          object.to_xml( xml ) if object.respond_to?(:to_xml)
        else
          # no columns were specified, so default to all (excluding relations)
          object.class.content_columns.collect{|c| c.name}.each do |field|
            xml.field(object.send(field), :name => field)
          end
        end
        
      end
      
      return doc
    end
    
    def self.make_fields(xml, value, field, stack = [] )
      if value.is_a?(Array)
        value.each do |v|
          make_fields( xml, v, field, stack )
        end
        return xml
      end
      
      # create basic field
      xml.field(value, :name => [stack + [field.indexed_name]].join("."), :boost => field.boost ) if field.include.empty? and value
      
      # create all appropriate subfields
      field.include.values.each do |subfield|
        make_fields( xml, value.send(subfield.attr_name), subfield, [stack + [field.indexed_name]] )
      end
      
      # create aliases
      field.aliases.each do |a|
        xml.field(value, :name => [stack + [a]].join("."), :boost => field.boost ) if field.include.empty? and value

        # create subfields for aliases
        field.include.values.each do |subfield|
          make_fields( xml, value, subfield, [stack + [a]] )
        end
      end
      
      # create sortable field
      xml.field(value, :name => "_sort-#{field.indexed_name}") if field.sortable?

      xml
    end
  end
end
