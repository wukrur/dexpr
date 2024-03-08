# DExpr - general and date expressions library
A little library for capturing and using various types of expressions in python.


## magic Op
magic Op captures expressions that use ParameterOp objects via operator overloads and creates a data structure
to represent operations captured:

```pytohn
_1 = ParameterOp(_index=0)
_2 = ParameterOp(_index=1)

expr1 = _1 + _2
```
here `expr1` is an instance of Op subclass that catures that an __add__ operator was called with the `_1` and `_2` 
variables. If we want to evaluate that expression with arbitrary arguments we use the `calc` function:

```python
assert calc(expr1, 1, 2) == 3
```
 The library supports all overloadable operators in python, including attribute access and calls:

```python
expr2 = _1.fn(_2)
```
if `expr2` is evaluated with an object that provides `fn` method as a first parameter it will call it and pass 
in the value of the second parameter

Op supports list and dict comprehensions
```python
expr = [i for i in lazy(range)(_0)]
assert calc(expr, 4) == [0, 1, 2, 3]
```
Note the`lazy` call to make the `range` function an Op

### DGen - date generators

The DGen simplifies producing lists of dates from an expression. The usual DGen expression
looks like this:

```python
last_sundays_in_march = '1980-01-01' < years.months[2].weeks[-1].sun < '2030-01-01'
```

The main parts of a DGen expression are the date expression itself that uses `years`, `months`, `weeks`, 
`weekdays`, `weekends`, `days` series to compose a rule for which date is it going to generate and 
bounding conditions that limit the series to specific bounds. The last bit does not have to be put into 
the expression itself but can be supplied when we ask it to generate:

```python
last_sundays_in_march = years.months[2].weeks[-1].sun
list_of_last_sundays_in_march = list(last_sundays_in_march(after='1980-01-01', before='2030-01-01'))
```

There is also a support for adding and subtracting tenors from dates:

```python
my_dates = months.days[14] + '1w'
```

Tenors supported are y, m, w, d and b. b is only valid if a calendar is supplied.


### dataclass Extensions

The `dataclassex` library allows the magic Ops and lamdas to be used as defaults for fields 
in dataclasses. The same can be done with properties, this library just makes it super simple 
to do:

```python
@dataclassex
class OrderWithLambda:
    order_date: date
    shipping_time: Tenor
    expected_delivery_date: date = lambda self: self.order_date + self.shipping_time

o = OrderWithLambda(order_date=make_date('2020-02-02'), shipping_time=Tenor('3d'))
assert o.expected_delivery_date == make_date('2020-02-05')
```

adding Op expressoins:

```python
Self = ParameterOp(_name='Self')

@dataclassex
class OrderWithOp:
    order_date: date
    shipping_time: Tenor
    expected_delivery_date: date = Self.order_date + Self.shipping_time

o = OrderWithLambda(order_date=make_date('2020-02-02'), shipping_time=Tenor('3d'))
assert o.expected_delivery_date == make_date('2020-02-05')
```

