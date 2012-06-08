"""
This module contains classes which represent database fields and
their derived values for display in the Gattini Data Explore.
"""

import numpy as N

from pylab import log10, pi

from matplotlib.dates import num2date, date2num

from db.query import per_image_fields, per_star_fields

def get_x_data(result, field):
    """
    Extract the data for a given field from a result recarray returned from the
    GDB. Convert any time fields into a numberical value.
    """
    field = field.split(".")[1]
    if field == 'time':
        data = date2num(result[field])
    else:
        data = result[field]
    return data

class Field:
    """
    This is the base class for GDE fields. Subclasses implement different
    behaviour for different kinds of fields.
    """

    def __init__(self, label):
        """
        Create a field with the given label. This label will be used to label
        the axes on GDE plots.
        """
        self.label = label

    def get_fields(self):
        """
        Return the database fields which must be queried to calculate the value
        for this field.
        """
        return self.fields

    def value(self, data, image=None):
        """
        Calculate the value of this field, given recarray of data retrieved
        from tehe GDB.

        This method must be implemented by all subclasses.
        """
        raise NotImplementedError

    def str_value(self, data):
        """
        Return the value as a string.
        """
        return str(self.value(data))

    def __str__(self):
        """
        Use the fields label as its string representation.
        """
        return self.label

    def __eq__(self, other):
        """
        Use field labels for defining equality of fields.
        """
        return self.label == other

class SimpleField(Field):
    """
    This is the most basic field. It takes a single database field and returns
    its values 'as is'.

    Subclasses of this can take the single database field and return it in a
    more appropriate manner.
    """

    def __init__(self, field):
        Field.__init__(self, field)
        self.fields = [field]

    def value(self, data, image=None):
        return get_x_data(data, self.fields[0])

class MedianField(Field):

    def __init__(self):
        Field.__init__(self, "30% Level")
        self.fields = []

    def value(self, data, images=None):
        ret = []
        for image in images:
            data = image[600][320:1280]
            thirty = data[int(0.3*len(data))]
            ret.append(thirty)
            print thirty
        return ret
        #return [N.median(N.asarray(image).flat) for image in images]

class RadianField(SimpleField):
    """
    A field which represent a value in radians. When represented as a string
    the values are converted to degrees for easy reading.
    """

    def str_value(self, data):
        """
        Return the value, in degrees, as a string
        """
        return str(180*SimpleField.value(self, data)/pi)

class TimeField(SimpleField):
    """
    A field which represent a time value. When represented as a string the
    values are converted to a full date string.
    """

    def str_value(self, data):
        return str(num2date(SimpleField.value(self, data)))

class ElevationField(SimpleField):
    """
    A field representing an elevation. Takes a zenith distance database field
    and returns values as elevation in degrees.
    """

    def __init__(self, field, label):
        SimpleField.__init__(self, field)
        Field.__init__(self, label)

    def value(self, data, image=None):
        return 90 - 180*get_x_data(data, self.fields[0])/N.pi

class ProductField(Field):
    """
    A field representing the product of two database fields.
    """

    def __init__(self, (field_a, field_b)):
        Field.__init__(self, "%s * %s" % (field_a, field_b))
        self.fields = (field_a, field_b)

    def value(self, data, image=None):
        return get_x_data(data, self.fields[0])*get_x_data(data, self.fields[1])

class SkyBrightness(Field):

    def __init__(self):
        Field.__init__(self, "Sky Brightness")
        self.fields = ["cam.name", "astrom.sky", "astrom.zmag",
                       "header.exposure", "imstat.mean", "header.temp"]

    def value(self, data, image=None):        
        cam = data['name']
        if type(cam) == N.recarray:
            cam = cam[0]
        pix_size = {"sky": N.sqrt(202000/4), "sbc": 11.3}[cam]        
        ex = data['exposure']
        sky = data['sky'].clip(0.0001, data['sky'].max())
        mean = data['mean'] 
        pix_mag = 2.5*log10(pix_size**2) 


        temp = data['temp'].copy()
        if type(cam) == N.recarray:
            temp[temp < -35] = -40
            temp[temp >= -35] = -30
            
            offset = ex.copy()
            offset[temp == -30] = 2.25*ex[temp == -30]
            offset[temp == -40] = 0.59*ex[temp == -40]
        else:
            offset = 0
        if cam == "sbc":
            offset = 68
        else:
            offset += 77.1
        return -2.5*log10(sky - offset) + data['zmag']  + pix_mag


class StarBrightness(Field):

    def __init__(self, label="Star Brightness"):
        Field.__init__(self, label)
        self.fields = ["astrom.zmag", "phot.mag3", "header.exposure"]

    def value(self, data, image=None):        
        return data['zmag'] + data['mag3'] - 25 -2.5*log10(data['exposure'])    

class StarBrightnessError(StarBrightness):

    def __init__(self):
        StarBrightness.__init__(self, "Star Brightness Error")
        self.fields.append("phot.vmag")

    def value(self, data, image=None):
        return StarBrightness.value(self, data) - data['vmag']


def make_field(field):
    """
    A function to take a database field and return an appropriate Field class.

    For time fields, a TimeField is created, for zenith distance fields, a
    RadianField is returned and a Simple field is returned for other fields.
    """

    if "time" in field:
        return TimeField(field)
    if "zd" in field:
        return RadianField(field)
    else:
        return SimpleField(field)
        
per_image_fields = [make_field(field) for field in per_image_fields] + \
                   [SkyBrightness(), ElevationField("header.sunzd", "Sun Elevation"),
                    ElevationField("header.moonzd", "Moon Elevation")]
per_star_fields = [make_field(field) for field in per_star_fields] + \
                  [StarBrightness(), StarBrightnessError()]
