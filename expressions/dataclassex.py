from abc import abstractmethod
from dataclasses import dataclass
from inspect import isfunction, signature

from expressions.magic import calc, Op


__all__ = ("dataclassex", 'DataclassEx')


class _BaseExDescriptor:
    def __init__(self, expr):
        self.expr = expr

    def __get__(self, instance, owner = None):
        if instance is not None:
            if (v := getattr(instance, self.cache_name, None)) is not None:
                return v

            v = self.__calc__(instance)
            setattr(instance, self.cache_name, v)
            return v
        elif owner:
            return self

    @abstractmethod
    def __calc__(self, instance): ...

    def __set__(self, instance, value):
        if value is not self and instance is not None:
            if not instance.__dataclass_params__.frozen:
                setattr(instance, self.cache_name, value)
            else:
                raise AttributeError(f'field {self.name} in {instance} is readonly')

    def __set_name__(self, owner, name):
        self.name = name
        self.cache_name = f'__cache_{self.name or id(self)}__'


class OpDescriptor(_BaseExDescriptor):
    def __calc__(self, instance):
        return calc(self.expr, instance)

class LambdaDescriptor(_BaseExDescriptor):
    def __calc__(self, instance):
        return self.expr(instance)


def _process_ops_and_lambdas(cls):
    cls.__annotations__.pop('Self', None)

    for k, a in cls.__annotations__.items():
        if (op := getattr(cls, k, None)) is not None:
            if isinstance(op, Op) and not issubclass(a, Op):
                descriptor = OpDescriptor(op)
                descriptor.__set_name__(cls, k)
                setattr(cls, k, descriptor)
            elif isfunction(op) and op.__name__ == '<lambda>':
                if len(signature(op).parameters) == 1:
                    descriptor = LambdaDescriptor(op)
                    descriptor.__set_name__(cls, k)
                    setattr(cls, k, descriptor)

    return cls


class DataclassEx:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        _process_ops_and_lambdas(cls)


def dataclassex(cls):
    return dataclass(_process_ops_and_lambdas(cls))
