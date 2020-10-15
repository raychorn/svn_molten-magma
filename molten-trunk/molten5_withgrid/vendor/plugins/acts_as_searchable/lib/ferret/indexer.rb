require 'ferret'

# Ferret modules are not included here;
# they pollute the namespace and can cause potential name conflicts

module MojoDNA::Searchable::Ferret
  # An indexer suitable for a low volume of writes (not multi-process safe)
  class Indexer
    # This can be overridden in environment.rb by calling Indexer::default_analyzer AnalyzerClass
    # or by using index_path in a model
    @@default_index_path = "#{RAILS_ROOT}/db/ferret_index"
    @@default_analyzer = ::Ferret::Analysis::StandardAnalyzer
    
    # TODO write a finalizer that closes all open indexes (?)
    # holder for open indexes
    @@index = {}
    
    # set the default analyzer for Searchable
    def self.default_analyzer(analyzer = nil)
      @@default_analyzer = analyzer unless analyzer.nil?
      @@default_analyzer
    end
    
    # set the default index path for Searchable
    def self.default_index_path(path = nil)
      @@default_index_path = path unless path.nil?
      @@default_index_path
    end
    
    # Open an IndexReader and assume the calling method knows what it's doing w/r/t re-use.
    def self.get_reader(path)
      # ::Ferret::Index::IndexReader.open(path)
      # Changed for compatibility with Ferret 0.10.4
      ::Ferret::Index::IndexReader.new(path)
    end
    
    # TODO look into getting rid of this as well as the @@index class var
    def self.get_index(path, options = {})
      options = { :analyzer => @@default_analyzer }.update( options ) if options.is_a?(Hash)
      
      # TODO figure out whether index is up-to-date
      return @@index[ path ] if @@index.has_key?( path ) # and @@index[ path ].send(:reader).latest?
      
      FileUtils.mkdir_p( path ) unless File.exists?( path )
      
      @@index[path] = open_index(path, options)
    end

    def self.delete_from_index( object )
      index = get_index( object.class.index_path, :analyzer => object.class.default_analyzer )
      index.delete( ::Ferret::Index::Term.new("_type-id", "#{object.class.to_s}-#{object.send( :id )}") )
      index.flush
      
      close_index( object.class.index_path )
    end
    
    def self.index( object )
      delete_from_index( object )
      
      index = get_index( object.class.index_path, :analyzer => object.class.default_analyzer.new )

      index << create_document( object )
      index.flush
      
      close_index( object.class.index_path )
    end
    
    def self.index_all(klass, use_tmp = true)
      index_created = Time.now
      base_path = klass.index_path
      base_path.chop! if base_path =~ /\/$/
      index_path = "#{base_path}.tmp" if use_tmp
      index_path = base_path unless use_tmp
      
      FileUtils.rm_rf( index_path ) if use_tmp and File.exists?( index_path )
      FileUtils.mkdir_p( index_path ) unless File.exists?( index_path )
      
      offset = 0
      quanta = 500
      include_ary = []
      begin
        include_ary = klass.searchable_fields.values.collect{|f| f.attr_name unless f.include.empty? or klass.reflections[f.attr_name.to_sym].nil?}.reject{|v| v.nil?}
      rescue NoMethodError
        # Rails 1.0 doesn't have klass.reflections, so assume everything is an association and not a method
        include_ary = klass.searchable_fields.values.collect{|f| f.attr_name unless f.include.empty?}.reject{|v| v.nil?}
      end
      # objects = klass.find(:all, :conditions => ["#{klass.table_name}.id > ?", offset], :limit => quanta, :include => include_ary)
      objects = klass.find(:all, :conditions => ["#{klass.table_name}.id > ?", offset], :include => include_ary)
      p "found #{objects.size}"
      begin
        
        # clean out existing documents from the index (provided we're not using a temporary index)
        # things that involve an IndexReader
        unless use_tmp
          puts "#{Time.now}: Deleting old documents"
          index = ::Ferret::Index::Index.new(:path => index_path)
          objects.each do |obj|
           query = ::Ferret::Search::TermQuery.new( Ferret::Index::Term.new("_type-id", "#{obj.class.to_s}-#{obj.send( :id )}") )
           index.query_delete( query )
          end
          index.close
        end

        # things that involve an IndexWriter
        puts "#{Time.now}: Adding documents to index"
        # writer = ::Ferret::Index::IndexWriter.new(index_path, :analyzer => klass.default_analyzer.new, :create_if_missing => true )
        # For compatibility with Ferret 0.10.4
        writer = ::Ferret::Index::IndexWriter.new(:path => index_path )
        writer.merge_factor = 100
        objects.each do |obj|
          writer << create_document( obj )
          p "adding #{obj.id}"
        end

        writer.close
        
        puts "#{Time.now}: (#{offset})"
        offset = objects.last.id
        puts "#{Time.now}: Querying for objects"
        objects = klass.find(:all, :conditions => ["#{klass.table_name}.id > ?", offset], :limit => quanta, :include => include_ary)
      end until objects.empty?


      # index stuff that was updated since index_created (if we can figure out what it is)
      if klass.column_names.include?("updated_at")
        while objects = klass.find(:all, :conditions => ["#{klass.table_name}.updated_at > ?", index_created], :include => include_ary) do
          break if objects.empty?
          index_created = Time.now
          
          # clean out existing documents from the index (provided we're not using a temporary index)
          # things that involve an IndexReader
          # TODO DRY (see above)
          unless use_tmp
            puts "#{Time.now}: Deleting new old documents"
            index = ::Ferret::Index::Index.new(:path => index_path)
            objects.each do |obj|
             query = ::Ferret::Search::TermQuery.new( Ferret::Index::Term.new("_type-id", "#{obj.class.to_s}-#{obj.send( :id )}") )
             index.query_delete( query )
            end
            index.close
          end

          # things that involve an IndexWriter
          puts "#{Time.now}: Adding new documents to index"
          writer = ::Ferret::Index::IndexWriter.new(index_path, :analyzer => klass.default_analyzer.new, :create_if_missing => true )
          writer.merge_factor = 100
          objects.each do |obj|
            writer << create_document( obj )
          end

          writer.close
        end
      end

      # optimize the index
      puts "#{Time.now}: Optimizing index"
      writer = ::Ferret::Index::IndexWriter.new(index_path, :analyzer => klass.default_analyzer.new )
      writer.optimize
      writer.close
      
      if use_tmp
        puts "#{Time.now}: Replacing existing index"
        FileUtils.mv( base_path, "#{base_path}.old", :force => true )
        FileUtils.mv( index_path, base_path, :force => true )
      end
      
      puts "#{Time.now}: Done."
    end
    
    def self.create_document(object)
      if object.class.searchable_fields or object.respond_to?(:to_doc)
        # create the doc according to searchable fields
        if object.class.searchable_fields
          doc = create_doc( object, object.class.searchable_fields )
        else
          doc = ::Ferret::Document::Document.new
        end

        # create / update the doc according to the to_doc method
        if object.respond_to?(:to_doc)
          doc = object.to_doc( doc )
        end
      else
        # create a doc using all of the database fields
        doc = ::Ferret::Document::Document.new
        # no columns were specified, so default to all (excluding relations)
        object.class.content_columns.collect{|c| c.name}.each do |field|
          doc_field = create_field( field, object.send(field) )
          doc << doc_field
        end
      end
      
      doc << Ferret::Document::Field.new( "_id", object.send( :id ), ::Ferret::Document::Field::Store::YES, ::Ferret::Document::Field::Index::UNTOKENIZED)
      doc << Ferret::Document::Field.new( "_type", object.class.to_s, ::Ferret::Document::Field::Store::YES, ::Ferret::Document::Field::Index::UNTOKENIZED)
      doc << ::Ferret::Document::Field.new( "_type-id", object.class.to_s + "-" + object.send( :id ).to_s, ::Ferret::Document::Field::Store::YES, ::Ferret::Document::Field::Index::UNTOKENIZED)
      
      doc
    end
    
    # helper method to create Ferret Fields
    # TODO refactor with named args
    def self.create_field(field_name, value, stored=false, tokenized=true)

      # TODO finish refactoring
      # options = { :stored => false, :tokenized => true }.update( options ) if options.is_a(Hash)
      
      
      # stored = stored ? ::Ferret::Document::Field::Store::YES : ::Ferret::Document::Field::Store::NO
      # Ferret 0.10.4
      stored = stored ? ::Ferret::Index::FieldInfo::Store::YES : ::Ferret::Index::FieldInfo::Store::NO
      # don't tokenize numeric fields
      tokenized = ( tokenized || !value.is_a?(Numeric) ) ? ::Ferret::Document::Field::Index::TOKENIZED : ::Ferret::Document::Field::Index::UNTOKENIZED
      
      ::Ferret::Document::Field.new(field_name.to_s, value.to_s, stored, tokenized)
    end
    
    def self.make_fields( value, field, stack = [] )
      fields = []

      if value.is_a?(Array)
        value.each do |v|
          fields += make_fields( v, field, stack )
        end
        return fields
      end
      
      # create basic field
      if field.include.empty? and value
        doc_field = create_field( [stack + [field.indexed_name]].join("."), value, field.stored?, field.tokenized? )
        doc_field.boost = field.boost
        fields << doc_field
      end
      
      # create all appropriate subfields
      field.include.values.each do |subfield|
        fields += make_fields( value.send(subfield.attr_name), subfield, [stack + [field.indexed_name]] )
      end
      
      # create aliases
      field.aliases.each do |a|
        if field.include.empty? and value
          doc_field = create_field( [stack + [a]].join("."), value, field.stored?, field.tokenized? )
          doc_field.boost = field.boost
          fields << doc_field
        end

        # create subfields for aliases
        field.include.values.each do |subfield|
          fields += make_fields( value, subfield, [stack + [a]] )
        end
      end
      
      # create sortable field
      if field.sortable?
        fields << create_field("_sort-#{field.indexed_name}", value, false, false )
      end

      fields
    end
    
    def self.create_doc(object, searchable_fields)
      # doc = Ferret::Document::Document.new
      # Ferret 0.10.4
      doc = Ferret::Document.new
      searchable_fields.values.each do |field|
        make_fields( object.send( field.attr_name ), field ).each do |f|
          doc << f
        end
      end
      
      doc
    end
    
    def self.optimize_index(path)
      index = get_index(path)
      index.optimize
      close_index(path)
    end
    
    def self.open_index(path, options = {})
      options = { :analyzer => @@default_analyzer }.update( options ) if options.is_a?(Hash)
      
      unless File.exists?( path )
        FileUtils.mkdir_p( path )
      end
      
      analyzer = options[:analyzer]
      analyzer.is_a?(::Ferret::Analysis::Analyzer) ? analyzer : analyzer.new
      index = ::Ferret::Index::Index.new(:path => path, :analyzer => analyzer )
      
      if block_given?
        yield index
        index.close
      else
        return index
      end
    end
    
    def self.close_index(path)
      index = get_index(path)
      @@index.delete( path )
      index.close
    end
  end
end
