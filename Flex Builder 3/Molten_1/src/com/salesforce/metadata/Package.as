package com.salesforce.metadata
{
	import com.salesforce.objects.SoapObject;
	
	import mx.collections.ArrayCollection;

	public class Package extends SoapObject
	{
		[ArrayElementType("PackageDirectory")]
		public var directory:ArrayCollection = new ArrayCollection();
    	public var version:String;
    	
    	public function Package(directory:ArrayCollection, version:String) {
    		this.directory = directory;
    		this.version = version;
    	}
	}
}